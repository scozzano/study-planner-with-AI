from typing import List

from pydantic import BaseModel


class SubjectType(BaseModel):
    id: str
    name: str
    type: str


class RequirerSubjectRecord(BaseModel):
    id: str
    min: str
    subjects: List[SubjectType]
