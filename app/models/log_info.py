from pydantic import BaseModel


class LogInfo(BaseModel):
    exception: str
    file: str
    line: int
