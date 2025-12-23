from pydantic import BaseModel

class ClassifyTextRequest(BaseModel):
    text: str
