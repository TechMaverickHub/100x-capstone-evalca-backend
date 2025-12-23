
from typing import Union

from fastapi import FastAPI, UploadFile, File

from services.ocr import extract_text_from_image

app = FastAPI(title="Eval CA Service")


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/ocr")
async def ocr_image(file: UploadFile = File(...)):
    text = await extract_text_from_image(file)
    return {
        "extracted_text": text
    }
