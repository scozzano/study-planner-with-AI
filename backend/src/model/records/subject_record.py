from pydantic import BaseModel


class SubjectRecord(BaseModel):
    id: str
    name: str
