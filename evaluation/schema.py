from typing import List

from pydantic import BaseModel


class EvaluateQuestionAnswer(BaseModel):
    question: str
    answer: str


class MarkingSchemePoint(BaseModel):
    point_code: str
    description: str
    max_marks: int


class MarkingScheme(BaseModel):
    total_marks: int
    scheme: List[MarkingSchemePoint]


class EvaluateQuestionAnswerExperimental(BaseModel):
    question: str
    answer: str
    marking_scheme: MarkingScheme