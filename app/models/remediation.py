from pydantic import BaseModel


class RemediationResult(BaseModel):
    recommended_fix: str
    code_suggestion: str = "Code suggestion unavailable"
    fix_confidence: str = "Unavailable"
    steps: list[str]
    prevention: str
