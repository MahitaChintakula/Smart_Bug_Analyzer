# from app.parser.log_parser import LogParser


# def main():

#     parser = LogParser()

#     stack_trace = """
# java.lang.NullPointerException

# at LoginService.java:45

# at UserController.java:18
# """

#     result = parser.parse(stack_trace)

#     print(result)


# if __name__ == "__main__":
#     main()
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.controller import BugController
from app.models.bug import Bug
from app.rag.knowledge_base import KnowledgeBase
from app.rag.retriever import RAGService
from app.services.chat_service import ChatService
from app.services.llm_service import LLMService, LLMServiceError
from app.services.ocr_service import OCRServiceError, extract_text_from_image


KNOWLEDGE_BASE_PATH = Path("data/resolved_bugs/resolved_bugs.json")


app = FastAPI(
    title="Smart Bug Analyzer API",
    description="AI-powered multi-agent bug analysis system",
    version="1.0.0",
)

# The React client runs on a separate development origin.  Keep the API
# contract unchanged while permitting that client to call /analyze.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class BugRequest(BaseModel):
    bug_report: str


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    analysis: dict[str, Any]
    messages: list[ChatMessage] = Field(default_factory=list)
    message: str


class KnowledgeBaseEntryRequest(BaseModel):
    """Fields accepted when manually adding a resolved historical bug."""

    bug_id: str | None = None
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    severity: str = Field(default="Medium", min_length=1, max_length=40)
    priority: str = Field(default="P3", min_length=1, max_length=20)
    module: str = Field(default="Unknown", max_length=120)
    exception: str = Field(default="Unknown", max_length=200)
    stack_trace: str = Field(default="", max_length=10000)
    root_cause: str = Field(default="Unknown", max_length=5000)
    resolution: str = Field(default="Unknown", max_length=5000)
    tags: list[str] = Field(default_factory=list)


def _knowledge_base() -> KnowledgeBase:
    return KnowledgeBase(str(KNOWLEDGE_BASE_PATH))


def _serialize_bug(bug: Bug, similarity: float | None = None) -> dict[str, Any]:
    if hasattr(bug, "model_dump"):
        serialized = bug.model_dump()
    else:  # pragma: no cover - compatibility with Pydantic v1
        serialized = bug.dict()

    if similarity is not None:
        serialized["similarity"] = round(float(similarity), 4)

    return serialized


def _index_stats(bugs: list[Bug]) -> dict[str, Any]:
    """Build a fresh FAISS index and report its current in-memory statistics."""
    if not bugs:
        return {
            "total_bugs": 0,
            "indexed_vectors": 0,
            "dimension": 384,
            "status": "ready",
        }

    rag_service = RAGService(bugs)
    index = rag_service.vector_store.index
    return {
        "total_bugs": len(bugs),
        "indexed_vectors": int(index.ntotal),
        "dimension": int(index.d),
        "status": "ready",
    }


@app.get("/")
def home():
    return {"message": "Smart Bug Analyzer API is running"}


@app.post("/analyze")
def analyze_bug(request: BugRequest):

    try:
        controller = BugController()

        result = controller.analyze(request.bug_report)

        if hasattr(result, "model_dump"):
            return result.model_dump()

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract-text")
async def extract_uploaded_text(file: UploadFile = File(...)):
    """Extract text from an uploaded screenshot for the existing analyzer flow."""
    content_type = (file.content_type or "").lower()
    if not content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Please upload a PNG, JPEG, WEBP, or GIF screenshot.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Please choose an image smaller than 10 MB.",
        )

    try:
        text = extract_text_from_image(image_bytes)
    except OCRServiceError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error

    if not text:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="No readable text was found in the screenshot.",
        )

    return {"text": text[:5000], "filename": file.filename or "screenshot"}


@app.get("/knowledge-base")
def list_knowledge_base(
    query: str = Query(default="", max_length=500),
    severity: str = Query(default="", max_length=40),
    module: str = Query(default="", max_length=120),
    limit: int = Query(default=500, ge=1, le=1000),
):
    """List, filter, or semantically search historical resolved bugs."""
    bugs = _knowledge_base().load_bugs()
    normalized_query = query.strip().lower()
    normalized_severity = severity.strip().lower()
    normalized_module = module.strip().lower()

    filtered_bugs = [
        bug
        for bug in bugs
        if (
            not normalized_severity
            or bug.severity.strip().lower() == normalized_severity
        )
        and (not normalized_module or bug.module.strip().lower() == normalized_module)
    ]

    if normalized_query and filtered_bugs:
        rag_service = RAGService(filtered_bugs)
        matches = rag_service.find_similar_bugs(
            normalized_query,
            k=min(limit, len(filtered_bugs)),
        )
        items = [_serialize_bug(match["bug"], match["similarity"]) for match in matches]
    else:
        items = [_serialize_bug(bug) for bug in filtered_bugs[:limit]]

    return {
        "items": items,
        "total": len(filtered_bugs),
        "query": query,
        "severities": sorted({bug.severity for bug in bugs}),
        "modules": sorted({bug.module for bug in bugs}),
    }


@app.get("/knowledge-base/stats")
def knowledge_base_stats():
    """Return counts and dimensions for a freshly rebuilt FAISS index."""
    bugs = _knowledge_base().load_bugs()
    stats = _index_stats(bugs)
    stats["severity_counts"] = dict(Counter(bug.severity for bug in bugs))
    stats["module_count"] = len({bug.module for bug in bugs})
    return stats


@app.post("/knowledge-base/rebuild")
def rebuild_knowledge_base():
    """Rebuild the in-memory FAISS index from the persisted JSON knowledge base."""
    bugs = _knowledge_base().load_bugs()
    stats = _index_stats(bugs)
    stats["message"] = "Knowledge base loaded and FAISS index rebuilt successfully."
    return stats


@app.post("/knowledge-base", status_code=status.HTTP_201_CREATED)
def add_knowledge_base_entry(request: KnowledgeBaseEntryRequest):
    """Add a resolved bug manually without creating duplicate entries."""
    knowledge_base = _knowledge_base()
    existing_bugs = knowledge_base.load_bugs()
    requested_id = (request.bug_id or "").strip()
    bug_id = requested_id or knowledge_base.next_bug_id()

    if any(bug.bug_id == bug_id for bug in existing_bugs):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Knowledge-base entry {bug_id} already exists.",
        )

    normalized_title = request.title.strip().lower()
    normalized_description = request.description.strip().lower()
    if any(
        bug.title.strip().lower() == normalized_title
        and bug.description.strip().lower() == normalized_description
        for bug in existing_bugs
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A knowledge-base entry with the same title and description already exists.",
        )

    entry = Bug(
        bug_id=bug_id,
        title=request.title.strip(),
        description=request.description.strip(),
        severity=request.severity.strip() or "Medium",
        priority=request.priority.strip() or "P3",
        module=request.module.strip() or "Unknown",
        exception=request.exception.strip() or "Unknown",
        stack_trace=request.stack_trace.strip(),
        root_cause=request.root_cause.strip() or "Unknown",
        resolution=request.resolution.strip() or "Unknown",
        tags=sorted({tag.strip() for tag in request.tags if tag.strip()}),
    )

    if not knowledge_base.append_bug(entry):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Knowledge-base entry {bug_id} already exists.",
        )

    # Rebuild from the persisted data so the new record is immediately part of
    # the same FAISS representation used by similarity search.
    updated_bugs = [*existing_bugs, entry]
    stats = _index_stats(updated_bugs)
    return {
        "message": f"Added {bug_id} to the knowledge base.",
        "bug": _serialize_bug(entry),
        "index": stats,
    }


@app.post("/chat")
def chat(request: ChatRequest):
    """Answer an explicit follow-up question for one completed analysis."""
    try:
        messages = [
            message.model_dump() if hasattr(message, "model_dump") else message.dict()
            for message in request.messages
        ]
        service = ChatService(llm_service=LLMService())
        answer = service.answer(request.analysis, messages, request.message)
        return {"message": answer}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except LLMServiceError as error:
        raise HTTPException(
            status_code=503,
            detail="The chatbot is temporarily unavailable. Please try again.",
        ) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Unable to process chatbot request.",
        ) from error
