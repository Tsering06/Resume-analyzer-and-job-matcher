import os
import logging
import pandas as pd

from resume_parser import extract_text_from_pdf, clean_text

RESUMES_FOLDER = os.path.join("Dataset", "resumes")
JOBS_FILE = os.path.join("Dataset", "jobs", "jobdataset.csv")

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def load_resumes(folder_path=RESUMES_FOLDER):
    resumes = []

    if not os.path.exists(folder_path):
        logging.warning(f"Resume folder not found: {folder_path}")
        return resumes

    files = [f for f in os.listdir(folder_path) if f.lower().endswith(".pdf")]
    logging.info(f"Found {len(files)} resume files")

    for file in files:
        path = os.path.join(folder_path, file)

        try:
            raw_text = extract_text_from_pdf(path)
            cleaned = clean_text(raw_text)

            if cleaned:
                resumes.append({
                    "filename": file,
                    "content": cleaned
                })

        except Exception as e:
            logging.error(f"Could not process {file}: {e}")

    logging.info(f"Loaded {len(resumes)} resumes")
    return resumes


def load_jobs(file_path=JOBS_FILE):
    jobs = []

    if not os.path.exists(file_path):
        logging.warning(f"Jobs file not found: {file_path}")
        return jobs

    try:
        df = pd.read_csv(file_path)

        for _, row in df.iterrows():
            description = " ".join([
                str(row.get("job descriptions", "")),
                str(row.get("Job Experience Required", "")),
                str(row.get("Location", "")),
                str(row.get("Role", ""))
            ])

            jobs.append({
                "title": row.get("title", "Unknown Role"),
                "description": description
            })

        logging.info(f"Loaded {len(jobs)} job descriptions")
        return jobs

    except Exception as e:
        logging.error(f"Failed loading jobs: {e}")
        return []