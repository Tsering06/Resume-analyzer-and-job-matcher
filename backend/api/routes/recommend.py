from fastapi import APIRouter, Form, HTTPException

from backend.matcher_faiss import matcher

router = APIRouter()


@router.post("/jobs")
async def recommend_jobs(resume_text: str = Form(...), top_k: int = Form(5)):
    """Return top-k job recommendations using FAISS semantic search."""
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Resume text cannot be empty.")
    top_k = max(1, min(top_k, 20))   # clamp between 1 and 20
    recommendations = matcher.recommend_jobs(resume_text, top_k=top_k)
    return {"recommendations": recommendations}
