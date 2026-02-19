import os
import uuid
from pathlib import Path

from fastapi import APIRouter, UploadFile, File

router = APIRouter()
IMAGES_DIR = Path(__file__).resolve().parent.parent.parent / "images"


@router.post("/images/upload")
async def upload_image(file: UploadFile = File(...)):
    ext = Path(file.filename).suffix or ".png"
    name = f"{uuid.uuid4().hex}{ext}"
    dest = IMAGES_DIR / name
    content = await file.read()
    dest.write_bytes(content)
    return {"filename": name, "url": f"/images/{name}"}


@router.get("/images")
def list_images():
    files = sorted(IMAGES_DIR.iterdir())
    return [
        {"filename": f.name, "url": f"/images/{f.name}"}
        for f in files
        if f.is_file() and f.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".wmf", ".x-wmf")
    ]
