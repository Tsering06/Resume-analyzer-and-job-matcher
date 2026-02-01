import os
from resume import extract_text_from_pdf, clean_text

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RESUME_PATH = os.path.join(BASE_DIR, "Dataset", "resumes")
JOB_PATH = os.path.join(BASE_DIR, "Dataset", "jobs")


def main():
    print("\n--- AI Resume Analyzer & Job Matcher ---\n")

    resumes = {}

    for file in os.listdir(RESUME_PATH):
        if file.lower().endswith(".pdf"):
            pdf_path = os.path.join(RESUME_PATH, file)
            text = extract_text_from_pdf(pdf_path)
            resumes[file] = clean_text(text)

    print(f"Loaded {len(resumes)} resumes")

    for name, text in resumes.items():
        print(f"\n📄 Resume: {name}")
        print(text[:300], "...")


if __name__ == "__main__":
    main()
