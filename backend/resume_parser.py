import pdfplumber


def parse_resume_pdf(file) -> str:
    """
    Accept a file-like object or path, return extracted text.
    Returns an empty string if extraction fails.
    """
    text_parts = []
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        print(f"[resume_parser] Error: {e}")
    return "\n".join(text_parts).strip()
