from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


def calculate_match_score(resume_text: str, job_text: str) -> float:
    """
    Compute similarity score between resume and job description.
    """
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([resume_text, job_text])

    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
    return round(similarity * 100, 2)


def extract_missing_skills(resume_text: str, job_text: str) -> list:
    """
    Identify important job keywords missing from resume.
    """
    job_words = set(job_text.split())
    resume_words = set(resume_text.split())

    missing = job_words - resume_words
    return list(missing)[:10] 
