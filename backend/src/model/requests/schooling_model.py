from pydantic import BaseModel


class SchoolingRequest(BaseModel):
    file: str
