import asyncio
import logging

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import status

from global_constants import SuccessMessage, ErrorMessage
from model import ClassifyTextRequest
from services.llm import detect_question_answer
from services.ocr import extract_text_from_image
from utils import response_schema

app = FastAPI(title="Eval CA Service")


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    text = await extract_text_from_image(file)

    return response_schema(SuccessMessage.RECORD_RETRIEVED.value, text, status.HTTP_200_OK)


logger = logging.getLogger(__name__)


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
