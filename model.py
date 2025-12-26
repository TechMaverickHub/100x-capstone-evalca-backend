from pydantic import BaseModel

class ClassifyTextRequest(BaseModel):
    text: str

class EvaluateQuestionAnswer(BaseModel):

    question: str
    answer: str
