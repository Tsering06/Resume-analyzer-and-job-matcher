import os
from typing import List
from dotenv import load_dotenv

# Loads .env file automatically
load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_AVAILABLE = bool(GROQ_API_KEY)

if GROQ_AVAILABLE:
    from groq import Groq
    client = Groq(api_key=GROQ_API_KEY)


def career_chat(resume_text: str, question: str) -> str:
    """Answer a single career question given the candidate's resume."""
    if not GROQ_AVAILABLE:
        return (
            "Career chat is unavailable — GROQ_API_KEY is not set. "
            "Add GROQ_API_KEY=your_key to your .env file."
        )
    prompt = f"""You are a friendly, expert career coach.
A candidate has shared their resume below.
Answer their question professionally and concisely (3-5 sentences max).

--- RESUME ---
{resume_text}
--------------

Question: {question}"""

    resp = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=512,
    )
    return resp.choices[0].message.content.strip()


def career_assistant(resume_text: str, questions: List[str]) -> List[dict]:
    """Answer multiple career questions."""
    return [
        {"question": q, "answer": career_chat(resume_text, q)}
        for q in questions
    ]