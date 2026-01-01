import asyncio
import logging

import os
from dotenv import load_dotenv
from fastapi import APIRouter, status, Depends

from auth.auth_util import get_current_user, require_role
from auth.model import User
from evaluation.schema import EvaluateQuestionAnswer
from core.global_constants import ErrorMessage, ErrorKeys, SuccessMessage, GlobalConstants
from services.evaluate import generate_ca_icmai_evaluation_prompt
from core.utils import response_schema

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/evaluate")
async def classify_text(payload: EvaluateQuestionAnswer, current_user: User = Depends(require_role(GlobalConstants.TEACHER_ROLE_ID))):
    question = payload.question.strip()
    answer = payload.answer.strip()

    MAX_QUESTION_WORDS = int(os.getenv("MAX_QUESTION_WORDS", 300))
    MAX_ANSWER_WORDS = int(os.getenv("MAX_ANSWER_WORDS", 700))

    question_word_count = len(question.split())
    answer_word_count = len(answer.split())

    if (
            question_word_count > MAX_QUESTION_WORDS
            or answer_word_count > MAX_ANSWER_WORDS
    ):
        return_data = {
            ErrorKeys.NON_FIELD_ERROR: (
                f"Question exceeds {MAX_QUESTION_WORDS} words or "
                f"Answer exceeds {MAX_ANSWER_WORDS} words."
            )
        }

        return response_schema(
            ErrorMessage.BAD_REQUEST.value,
            return_data,
            status.HTTP_400_BAD_REQUEST
        )

    if not question or not answer:
        return_data = {
            ErrorKeys.NON_FIELD_ERROR: ErrorMessage.BAD_REQUEST.value
        }

        return response_schema(
            ErrorMessage.BAD_REQUEST.value,
            return_data,
            status.HTTP_400_BAD_REQUEST
        )

    response = await asyncio.to_thread(generate_ca_icmai_evaluation_prompt, question, answer)
    logger.info(f"LLM response: {response}")

    return response_schema(
        SuccessMessage.RECORD_RETRIEVED.value,
        response,
        status.HTTP_200_OK
    )
