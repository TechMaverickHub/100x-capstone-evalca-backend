import os
from typing import List

from dotenv import load_dotenv
from fastapi import UploadFile, File, APIRouter, status, Depends

from auth.auth_util import require_role
from auth.model import User
from core.global_constants import ErrorKeys, ErrorMessage, SuccessMessage, GlobalConstants
from ocr.ocr_utils import extract_text_from_image
from core.utils import response_schema

load_dotenv()
router = APIRouter()

@router.post("/ocr-question")
async def ocr_question(files: List[UploadFile] = File(...), current_user: User = Depends(require_role(GlobalConstants.TEACHER_ROLE_ID))):
    if len(files) > int(os.getenv("MAXIMUM_QUESTION_FILES")):
        return_data = {
            ErrorKeys.NON_FIELD_ERROR: ErrorMessage.MAXIMUM_QUESTION_FILES_ALLOWED.value
        }

        return response_schema(
            ErrorMessage.BAD_REQUEST.value,
            return_data,
            status.HTTP_400_BAD_REQUEST
        )

    individual_results = []
    combined_text_parts = []
    confidence_scores = []

    for file in files:
        extracted_text = await extract_text_from_image(file)

        text = extracted_text.get("text", "")
        confidence = extracted_text.get("confidence")

        individual_results.append({
            "filename": file.filename,
            "text": text,
            "confidence": confidence
        })

        if text:
            combined_text_parts.append(text)

        if confidence is not None:
            confidence_scores.append(float(confidence))

    # Combine all text
    combined_text = "\n\n".join(combined_text_parts)

    # Compute average confidence
    average_confidence = (
        round(sum(confidence_scores) / len(confidence_scores), 2)
        if confidence_scores
        else 0.0
    )

    final_result = {
        "individual_results": individual_results,
        "combined_text": combined_text,
        "average_confidence": average_confidence,
        "total_files": len(files)
    }

    return response_schema(
        SuccessMessage.RECORD_RETRIEVED.value,
        final_result,
        status.HTTP_200_OK
    )


@router.post("/ocr-answer")
async def ocr_answer(files: List[UploadFile] = File(...), current_user: User = Depends(require_role(GlobalConstants.TEACHER_ROLE_ID))):
    if len(files) > int(os.getenv("MAXIMUM_ANSWER_FILES")):
        return_data = {
            ErrorKeys.NON_FIELD_ERROR: ErrorMessage.MAXIMUM_ANSWER_FILES_ALLOWED.value
        }

        return response_schema(
            ErrorMessage.BAD_REQUEST.value,
            return_data,
            status.HTTP_400_BAD_REQUEST
        )

    individual_results = []
    combined_text_parts = []
    confidence_scores = []

    for file in files:
        extracted_text = await extract_text_from_image(file)

        text = extracted_text.get("text", "")
        confidence = extracted_text.get("confidence")

        individual_results.append({
            "filename": file.filename,
            "text": text,
            "confidence": confidence
        })

        if text:
            combined_text_parts.append(text)

        if confidence is not None:
            confidence_scores.append(float(confidence))

    # Combine all text
    combined_text = "\n\n".join(combined_text_parts)

    # Compute average confidence
    average_confidence = (
        round(sum(confidence_scores) / len(confidence_scores), 2)
        if confidence_scores
        else 0.0
    )

    final_result = {
        "individual_results": individual_results,
        "combined_text": combined_text,
        "average_confidence": average_confidence,
        "total_files": len(files)
    }

    return response_schema(
        SuccessMessage.RECORD_RETRIEVED.value,
        final_result,
        status.HTTP_200_OK
    )