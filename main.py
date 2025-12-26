import asyncio
import logging
import os
from typing import List

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware

from global_constants import SuccessMessage, ErrorMessage, ErrorKeys
from model import ClassifyTextRequest
from services.llm import detect_question_answer
from services.ocr import extract_text_from_image
from utils import response_schema

load_dotenv()
app = FastAPI(title="Eval CA Service")
origins = [
    os.getenv("FRONTEND_BASE_API"),
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger(__name__)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    text = await extract_text_from_image(file)

    return response_schema(SuccessMessage.RECORD_RETRIEVED.value, text, status.HTTP_200_OK)


@app.post("/ocr-question")
async def ocr_question(files: List[UploadFile] = File(...)):
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


@app.post("/ocr-answer")
async def ocr_answer(files: List[UploadFile] = File(...)):

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


@app.post("/classify-text")
async def classify_text(payload: ClassifyTextRequest):
    text = payload.text.strip()

    if not text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text cannot be empty"
        )

    logger.info("Received text for classification")

    try:
        # Run blocking LLM call in threadpool
        response = await asyncio.to_thread(detect_question_answer, text)
        logger.info(f"LLM response: {response}")

    except Exception as e:
        logger.exception("LLM processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM processing failed"
        )

    if not response.get("question") or not response.get("answer"):
        return response_schema(
            response,
            None,
            status.HTTP_200_OK
        )

    return response_schema(
        SuccessMessage.RECORD_RETRIEVED.value,
        response,
        status.HTTP_200_OK
    )
