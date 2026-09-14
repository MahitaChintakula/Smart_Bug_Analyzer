from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter()


class BugRequest(BaseModel):
    bug_report: str


@router.get("/")
def home():
    return {"message": "Smart Bug Analyzer API is running"}


@router.post("/analyze")
def analyze_bug(request: BugRequest):

    return {
        "status": "success",
        "message": "Bug received successfully",
        "bug_report": request.bug_report,
    }
