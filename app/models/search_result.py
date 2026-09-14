from pydantic import BaseModel


class SearchResult(BaseModel):
    bug_id: str
    title: str
    severity: str
    priority: str
    similarity_score: float
