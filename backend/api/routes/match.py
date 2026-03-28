import tempfile, os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from backend.matcher_faiss import matcher
from backend.resume_data_loader import extract_text_from_pdf, extract_text_from_linkedin

router = APIRouter()

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        text = extract_text_from_pdf(tmp_path)
    finally:
        os.unlink(tmp_path)
    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text from PDF.")
    results = matcher.match_resume(text)
    return {"resume_text": text[:500] + "...", "matches": results}

@router.post("/linkedin")
async def parse_linkedin_profile(profile_url: str = Form(...)):
    text = extract_text_from_linkedin(profile_url)
    if not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract text. Make sure profile is public.")
    results = matcher.match_resume(text)
    return {"linkedin_text": text[:500] + "...", "matches": results}

@router.post("/paste")
async def paste_resume(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=422, detail="Resume text cannot be empty.")
    results = matcher.match_resume(text)
    return {"resume_text": text[:500] + "...", "matches": results}