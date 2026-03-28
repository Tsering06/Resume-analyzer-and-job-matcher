from fastapi import APIRouter, Form, HTTPException

from backend.services.llm_service import career_chat

router = APIRouter()


@router.post("/ask")
async def ask_chat(question: str = Form(...), resume_text: str = Form(...)):
    """Career-advice chatbot powered by GPT-4o-mini."""
    if not question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty.")
    if not resume_text.strip():
        raise HTTPException(status_code=422, detail="Resume text cannot be empty.")
    answer = career_chat(resume_text, question)
    return {"question": question, "answer": answer}
