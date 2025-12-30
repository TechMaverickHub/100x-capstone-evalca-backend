from pydantic import BaseModel


class EvaluateQuestionAnswer(BaseModel):
    question: str
    answer: str