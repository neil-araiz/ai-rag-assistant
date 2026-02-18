from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    # Just return file name for now
    return {"filename": file.filename}
