from pydantic import BaseModel


class Bug(BaseModel):
    bug_id: str
    title: str
    description: str
    severity: str
    priority: str
    module: str
    exception: str
    stack_trace: str
    root_cause: str
    resolution: str
    tags: list[str]
