import os
from typing import Tuple, List

import pandas as pd
import pdfplumber
import requests
from bs4 import BeautifulSoup

DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),   # project root
    "Dataset", "jobs", "jobdataset.csv"
)

# ── Job loading ───────────────────────────────────────────────────────────────

def load_jobs(csv_path: str = DATASET_PATH) -> Tuple[List[str], List[str]]:
    """
    Load jobs from CSV.  Tries multiple common column-name conventions.
    Returns (job_texts, job_titles).
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(
            f"Job dataset not found at {csv_path}. "
            "Please place jobdataset.csv in Dataset/jobs/"
        )

    df = pd.read_csv(csv_path).fillna("")
    df.columns = df.columns.str.strip()  # ← add this line

    # ── find title column ─────────────────────────────────────────────────────
    title_candidates = ["Title", "title", "job_title", "Job Title", "position"]
    title_col = next((c for c in title_candidates if c in df.columns), None)
    if title_col is None:
        raise ValueError(
            f"Cannot find a title column. Available columns: {list(df.columns)}"
        )

    # ── find description column (optional) ────────────────────────────────────
    desc_candidates = [
        "job descriptions", "description", "Description",
        "job_description", "Job Description", "details",
    ]
    desc_col = next((c for c in desc_candidates if c in df.columns), None)

    if desc_col:
        job_texts = (df[title_col] + " " + df[desc_col]).tolist()
    else:
        job_texts = df[title_col].tolist()

    job_titles = df[title_col].tolist()
    return job_texts, job_titles


# ── PDF extraction ────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from every page of a PDF resume."""
    text_parts = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"[PDF] Error reading {file_path}: {e}")
    return "\n".join(text_parts).strip()


# ── LinkedIn scraping ─────────────────────────────────────────────────────────

_LINKEDIN_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

def extract_text_from_linkedin(profile_url: str, timeout: int = 10) -> str:
    """
    Scrape visible text from a *public* LinkedIn profile.
    Note: LinkedIn actively blocks scrapers; results may be limited.
    """
    try:
        resp = requests.get(profile_url, headers=_LINKEDIN_HEADERS, timeout=timeout)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        tags = soup.find_all(["h1", "h2", "h3", "p", "span", "li"])
        text = " ".join(t.get_text(separator=" ", strip=True) for t in tags)
        return text.strip()
    except requests.RequestException as e:
        print(f"[LinkedIn] Network error for {profile_url}: {e}")
        return ""
    except Exception as e:
        print(f"[LinkedIn] Unexpected error: {e}")
        return ""
