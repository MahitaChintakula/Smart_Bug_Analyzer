from pydantic import BaseModel


class TriageResult(BaseModel):
    severity: str
    priority: str
    reason: str
