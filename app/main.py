import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.inference import Candidate, run_on_device_inference
from app.storage import iter_jsonl, log_feedback, log_photo

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="CalorieTracker")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class CandidateOut(BaseModel):
    label: str
    confidence: float


class PhotoLogResponse(BaseModel):
    log_id: str
    candidates: List[CandidateOut]
    confirmation_required: bool = True


class ConfirmationPayload(BaseModel):
    log_id: str
    confirmed_label: str = Field(..., min_length=1)
    portion_grams: float = Field(..., gt=0)


class ConfirmationResponse(BaseModel):
    log_id: str
    confirmed_label: str
    portion_grams: float
    status: str


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    return HTMLResponse((STATIC_DIR / "index.html").read_text(encoding="utf-8"))


@app.post("/photo-log", response_model=PhotoLogResponse)
async def create_photo_log(photo: UploadFile = File(...)) -> PhotoLogResponse:
    payload = await photo.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Photo payload is empty.")
    candidates = run_on_device_inference(photo.filename or "upload", payload)
    log_id = str(uuid.uuid4())
    log_photo(
        {
            "log_id": log_id,
            "filename": photo.filename,
            "content_type": photo.content_type,
            "status": "pending_confirmation",
            "candidates": [candidate.__dict__ for candidate in candidates],
        }
    )
    return PhotoLogResponse(
        log_id=log_id,
        candidates=[CandidateOut(label=c.label, confidence=c.confidence) for c in candidates],
    )


@app.post("/photo-log/confirm", response_model=ConfirmationResponse)
def confirm_photo_log(payload: ConfirmationPayload) -> ConfirmationResponse:
    logs = iter_jsonl(Path(BASE_DIR / "data" / "photo_logs.jsonl"))
    if not any(entry.get("log_id") == payload.log_id for entry in logs):
        raise HTTPException(status_code=404, detail="Log entry not found.")

    log_feedback(
        {
            "log_id": payload.log_id,
            "confirmed_label": payload.confirmed_label,
            "portion_grams": payload.portion_grams,
        }
    )
    log_photo(
        {
            "log_id": payload.log_id,
            "status": "confirmed",
            "confirmed_label": payload.confirmed_label,
            "portion_grams": payload.portion_grams,
        }
    )
    return ConfirmationResponse(
        log_id=payload.log_id,
        confirmed_label=payload.confirmed_label,
        portion_grams=payload.portion_grams,
        status="confirmed",
    )


@app.get("/photo-log/recent")
def recent_logs() -> List[dict]:
    return iter_jsonl(Path(BASE_DIR / "data" / "photo_logs.jsonl"))
