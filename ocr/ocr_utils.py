import io
import os
from typing import Dict

import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv
from fastapi import UploadFile
from google.cloud import vision
from paddleocr import PaddleOCR

load_dotenv()
# Initialize PaddleOCR ONCE (important)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en"
)

os.environ["DISABLE_MODEL_SOURCE_CHECK"] = os.getenv("DISABLE_MODEL_SOURCE_CHECK")

async def extract_text_from_image(file: UploadFile):
    image_bytes = await file.read()
    return extract_text_from_image_with_paddle_ocr(image_bytes)

async def extract_text_from_image_with_paddle_ocr(file) -> dict:
    image_bytes = await file.read()

    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    image_np = np.array(image)
    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    ocr_result = ocr.ocr(image_np)

    extracted_lines = []
    confidences = []

    for page in ocr_result:
        texts = page.get("rec_texts", [])
        scores = page.get("rec_scores", [])

        for text, score in zip(texts, scores):
            if text.strip():
                extracted_lines.append(text)
                confidences.append(float(score))

    full_text = "\n".join(extracted_lines)

    avg_confidence = (
        round(sum(confidences) / len(confidences), 2)
        if confidences else 0.0
    )

    return {
       "text": full_text.strip(),
        "confidence": avg_confidence
    }


def split_question_answer(text: str):
    """
    Simple heuristic:
    - Question usually ends with '?' or 'Marks'
    - Everything after is treated as answer
    """

    print(text)

    lines = text.split("\n")

    question_lines = []
    answer_lines = []
    question_complete = False

    for line in lines:
        if not question_complete:
            question_lines.append(line)
            if "?" in line or "marks" in line.lower():
                question_complete = True
        else:
            answer_lines.append(line)

    return (
        " ".join(question_lines),
        " ".join(answer_lines)
    )



client = vision.ImageAnnotatorClient.from_service_account_file(os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

def extract_text_google_vision_depreceated(image_bytes: bytes) -> Dict:
    image = vision.Image(content=image_bytes)

    response = client.text_detection(image=image)
    annotations = response.text_annotations

    if response.error.message:
        raise RuntimeError(response.error.message)

    if not annotations:
        return {
            "text": "",
            "confidence": 0.0
        }

    # First annotation = full text
    full_text = annotations[0].description

    # Google Vision does NOT give a single confidence score reliably
    avg_confidence = None

    return {
        "text": full_text,
        "confidence": avg_confidence
    }