from fastapi import APIRouter, File, UploadFile, HTTPException
import json
import os
from app.retsinformation.splitter import Split
import logging

router = APIRouter()


logging.basicConfig(level=logging.INFO)


def save_file(file: UploadFile, file_location: str):
    if not os.path.exists(file_location):
        with open(file_location, "wb") as f:
            f.write(file)
        logging.info(f"File saved at {file_location}")
    else:
        logging.info(f"File {file_location} already exists, skipping save.")


def load_json_file(json_file_path: str):
    try:
        with open(json_file_path, "r") as json_file:
            return json.load(json_file)
    except Exception as e:
        logging.error(f"Error loading JSON file: {e}")
        raise HTTPException(status_code=500, detail="Error processing file")


@router.post("/retsinformation/split")
async def split_pdf_retsinformation(file: UploadFile = File(...)):
    file_location = f"app/retsinformation/data/{file.filename}"
    save_file(await file.read(), file_location)

    pdf_title = os.path.splitext(file.filename)[0]
    json_output_file = f"app/retsinformation/data/{pdf_title}_chunks.json"

    if os.path.exists(json_output_file):
        result = load_json_file(json_output_file)
    else:
        splitter = Split(
            input_pdf=file_location,
            pdf_title=pdf_title,
            markdown_output_file=f"app/retsinformation/data/{pdf_title}.md",
            json_output_file=json_output_file,
        )
        splitter.run()
        result = load_json_file(json_output_file)

    return result
