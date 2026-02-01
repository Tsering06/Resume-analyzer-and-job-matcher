import pdfplumber
import re
import nltk
from nltk.corpus import stopwords

nltk.download("stopwords")

STOPWORDS = set(stopwords.words("english"))

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract raw text from a PDF resume.
    """
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "
    return text.lower()


def clean_text(text: str) -> str:
    """
    Clean resume text for NLP processing.
    """
    text = re.sub(r"[^a-zA-Z ]", " ", text)
    tokens = text.split()
    tokens = [word for word in tokens if word not in STOPWORDS and len(word) > 2]
    return " ".join(tokens)
