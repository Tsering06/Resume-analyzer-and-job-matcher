import os
import pickle
import tempfile
import numpy as np
import streamlit as st
from sentence_transformers import SentenceTransformer

from resume_data_loader import load_jobs
from matcher import ResumeMatcher
from llm_feedback import generate_feedback, skill_gap_analysis
from resume_parser import extract_text_from_pdf, clean_text


# ---------------- PAGE CONFIG ---------------- #

st.set_page_config(
    page_title="AI Resume Matcher",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ---------------- STYLING ---------------- #

st.markdown("""
<style>
body {
    background-color: #0f172a;
}

h1, h2, h3 {
    color: #e2e8f0;
}

.stMetric {
    background-color: #1e293b;
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)


# ---------------- PATHS ---------------- #

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOBS_FILE = os.path.join(BASE_DIR, "Dataset", "jobs", "jobdataset.csv")


# ---------------- CACHED ---------------- #

@st.cache_resource
def load_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_data
def load_jobs_data():
    return load_jobs(JOBS_FILE)


@st.cache_data
def load_embeddings():
    with open("embeddings.pkl", "rb") as f:
        names, texts, embeddings = pickle.load(f)
    return names, texts, embeddings


# ---------------- LOAD DATA ---------------- #

jobs = load_jobs_data()
resume_names, resume_texts, resume_embeddings = load_embeddings()

if not jobs:
    st.warning("No jobs found.")
    st.stop()

model = load_model()
matcher = ResumeMatcher(model)


# ---------------- SIDEBAR ---------------- #

with st.sidebar:
    st.title("⚙️ Controls")

    job_titles = [job["title"] for job in jobs]
    selected_job = st.selectbox("Select Job Role", job_titles)

    top_k = st.slider("Top Results", 3, 10, 5)

    st.markdown("---")
    st.caption("AI Resume Matcher v1.0")


job_description = next(
    job["description"] for job in jobs if job["title"] == selected_job
)


# ---------------- HEADER ---------------- #

st.markdown("""
#  AI Resume Analyzer
### Match candidates intelligently using AI
""")


# ---------------- RANKING ---------------- #

st.markdown("## 🎯 Top Candidates")

with st.spinner("🔍 Searching best matches..."):
    ranked = matcher.rank_resumes(
        resume_names,
        resume_embeddings,
        job_description
    )

top_results = ranked[:top_k]

scores = []

for rank, (name, score) in enumerate(top_results, start=1):
    
    # Ensure score is a Python float
    score = float(score)
    scores.append(score)

    with st.container():

        st.markdown(f"### #{rank} — {name}")

        col1, col2 = st.columns([3, 1])

        with col1:
            # Safely show progress bar
            st.progress(min(score, 1.0))

        with col2:
            st.metric("Score", f"{score:.2%}")

        if score > 0.75:
            st.success("Strong Match")
        elif score > 0.5:
            st.warning("Moderate Match")
        else:
            st.error("Weak Match")

        if st.button("View Feedback", key=name):

            idx = resume_names.index(name)
            resume_text = resume_texts[idx]

            with st.spinner("Analyzing resume..."):
                feedback = generate_feedback(resume_text, job_description)

            st.success("Feedback Ready")
            st.write(feedback)

        st.markdown("---")


# ---------------- DASHBOARD ---------------- #

st.markdown("##  Insights")

col1, col2, col3 = st.columns(3)

col1.metric("Avg Score", round(float(np.mean(scores)), 2))
col2.metric("Top Score", round(float(max(scores)), 2))
col3.metric("Candidates", len(resume_names))


# ---------------- UPLOAD ---------------- #

st.markdown("---")
st.markdown("##  Test Your Resume")

uploaded_file = st.file_uploader("Upload a PDF resume", type=["pdf"])

if uploaded_file:

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(uploaded_file.read())
        temp_path = tmp.name

    raw_text = extract_text_from_pdf(temp_path)
    cleaned = clean_text(raw_text)

    if cleaned:

        with st.spinner("Analyzing resume..."):
            score = float(matcher.match_single_resume(cleaned, job_description))  # <-- ensure float

        st.success("Analysis complete")
        st.metric("Match Score", f"{score:.2%}")

        # -------- SKILL GAP -------- #

        matched, missing = skill_gap_analysis(cleaned, job_description)

        st.markdown("### 🧩 Skill Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.success("Matched Skills")
            st.write(", ".join(matched) if matched else "None")

        with col2:
            st.error("Missing Skills")
            st.write(", ".join(missing) if missing else "None")

        # -------- FEEDBACK -------- #

        if st.button("Generate AI Feedback"):

            with st.spinner("Generating feedback..."):
                feedback = generate_feedback(cleaned, job_description)

            st.markdown("AI Feedback")
            st.write(feedback)

# ---------------- FOOTER ---------------- #

st.markdown("---")
st.caption("Built with Sentence-BERT • FAISS • Streamlit")