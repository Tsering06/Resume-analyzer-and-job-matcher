import pdfplumber
import re

MAX_RESUME_LENGTH = 5000


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from a PDF file."""
    pages_text = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages_text.append(text)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

    return "\n".join(pages_text)


def clean_text(text: str) -> str:
    """Basic text cleaning."""
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)

    if len(text) > MAX_RESUME_LENGTH:
        text = text[:MAX_RESUME_LENGTH]
    return text.strip()