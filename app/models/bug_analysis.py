from pydantic import BaseModel
from typing import List


class BugAnalysis(BaseModel):
    bug_report: str
    exception: str | None = None
    file: str | None = None
    line: int | None = None

    similar_bugs: List[dict]

    root_cause: str
    severity: str
    priority: str
    recommended_fix: str
