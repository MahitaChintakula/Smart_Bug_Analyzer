from pydantic import BaseModel


class RootCauseResult(BaseModel):
    root_cause: str
    explanation: str
    confidence: float
