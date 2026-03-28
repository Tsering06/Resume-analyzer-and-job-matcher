from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import match, chat, recommend

app = FastAPI(
    title="Resume Analyzer & Job Matcher API",
    description="Parse resumes, match jobs with FAISS, and get AI career advice.",
    version="2.0.0",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Streamlit frontend (any localhost port) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to ["http://localhost:8501"] in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(match.router,     prefix="/match",     tags=["Match"])
app.include_router(recommend.router, prefix="/recommend", tags=["Recommend"])
app.include_router(chat.router,      prefix="/chat",      tags=["Chat"])


@app.get("/", tags=["Health"])
def root():
    return {"message": "Resume Analyzer & Job Matcher API is running ✅"}


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}