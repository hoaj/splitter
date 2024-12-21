import json
import os

from fastapi import APIRouter, File, UploadFile

from app.retsinformation.splitter import Split

router = APIRouter()


@router.post("/retsinformation/split")
async def split_pdf_retsinformation(file: UploadFile = File(...)):
    file_location = f"app/retsinformation/data/{file.filename}"
    with open(file_location, "wb") as f:
        f.write(await file.read())

    pdf_title = os.path.splitext(file.filename)[0]
    json_output_file = f"app/retsinformation/data/{pdf_title}_chunks.json"

    # Check if the chunks file already exists
    if os.path.exists(json_output_file):
        with open(json_output_file, "r") as json_file:
            result = json.load(json_file)
    else:
        splitter = Split(
            input_pdf=file_location,
            pdf_title=pdf_title,
            markdown_output_file=f"app/retsinformation/data/{pdf_title}.md",
            json_output_file=json_output_file,
        )
        splitter.run()

        with open(json_output_file, "r") as json_file:
            result = json.load(json_file)

    return result
