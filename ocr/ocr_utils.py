import os

from dotenv import load_dotenv
from paddleocr import PaddleOCR
from PIL import Image
import numpy as np
import io
import cv2

load_dotenv()
# Initialize PaddleOCR ONCE (important)
ocr = PaddleOCR(
    use_angle_cls=True,
    lang="en"
)

os.environ["DISABLE_MODEL_SOURCE_CHECK"] = os.getenv("DISABLE_MODEL_SOURCE_CHECK")

async def extract_text_from_image(file) -> dict:
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