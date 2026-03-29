import sys
import os
import requests
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

API_BASE = "http://127.0.0.1:8000"
TIMEOUT  = 30

st.set_page_config(
    page_title="Resume Analyzer & Job Matcher",
    page_icon="📄",
    layout="wide",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0f172a; }
    [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
    .match-card {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        color: #e2e8f0;
    }
    .match-title { color: #a5b4fc; font-size: 1rem; font-weight: bold; }
    .match-snippet { color: #94a3b8; font-size: 0.85rem; }
    .score-pill {
        display: inline-block;
        background: #4f46e5;
        color: #fff;
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.78rem;
        font-weight: 600;
        margin-left: 8px;
    }
</style>
""", unsafe_allow_html=True)

if "resume_text"  not in st.session_state: st.session_state.resume_text  = ""
if "matches"      not in st.session_state: st.session_state.matches      = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []

def check_api():
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False

def render_matches(matches):
    if not matches:
        st.info("No matches returned.")
        return
    for m in matches:
        pct     = int(m.get("similarity", 0) * 100)
        snippet = m.get("snippet", "")
        rank    = m.get("rank", "?")
        title   = m.get("title", "Unknown Role")
        st.markdown(f"""
<div class="match-card">
  <div class="match-title">#{rank} &nbsp; {title}
    <span class="score-pill">{pct}% match</span>
  </div>
  <div class="match-snippet">{snippet}</div>
</div>""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("##  Resume Analyzer")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        [" Home",
         " Upload PDF",
         " LinkedIn URL",
         " Paste Resume",
         " Top Recommendations",
         " Career Chat"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    api_ok = check_api()
    if api_ok:
        st.success("API connected")
    else:
        st.error(" API offline\nRun:\nuvicorn backend.api.main:app --reload")
    if st.session_state.resume_text:
        st.markdown("---")
        st.caption("📋 Resume loaded")
        st.caption(st.session_state.resume_text[:120] + "...")
if page == " Home":
    st.title(" Resume Analyzer & Job Matcher")
    st.markdown("Welcome! Use the sidebar to get started.")
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    col1.metric("Input methods", "3", "PDF / LinkedIn / Paste")
    col2.metric("Matching engine", "FAISS", "Cosine similarity")
    col3.metric("AI advisor", "Llama 3", "via Groq")
    st.markdown("---")
    st.markdown("""
**How it works:**
1. Upload your resume (PDF, paste text, or LinkedIn URL)
2. The app matches your skills to 500+ jobs using semantic AI
3. Get ranked job recommendations
4. Ask career advice questions in the Chat tab
    """)
elif page == " Upload PDF":
    st.title(" Upload PDF Resume")
    st.markdown("Upload your resume as a PDF file to get instant job matches.")
    st.markdown("---")

    uploaded = st.file_uploader(
        "Choose your PDF resume",
        type=["pdf"],
        help="Max 200MB. Must be a text-based PDF (not scanned image)."
    )

    if uploaded is not None:
        st.success(f" File received: **{uploaded.name}** ({uploaded.size} bytes)")

        if not api_ok:
            st.error(" API is offline. Start it first.")
        else:
            if st.button(" Analyze PDF"):
                with st.spinner("Extracting text and matching jobs..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/match/upload",
                            files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                            timeout=TIMEOUT,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.resume_text = data.get("resume_text", "")
                            st.session_state.matches     = data.get("matches", [])
                            st.success(" Resume analyzed successfully!")
                        else:
                            detail = resp.json().get("detail", resp.text)
                            st.error(f"Error {resp.status_code}: {detail}")
                    except requests.RequestException as e:
                        st.error(f"Connection error: {e}")

    if st.session_state.matches:
        st.markdown("---")
        st.subheader(" Top Matching Jobs")
        render_matches(st.session_state.matches)
elif page == " LinkedIn URL":
    st.title(" LinkedIn Profile Matcher")
    st.warning(" LinkedIn restricts scraping. Use a fully public profile or use Paste Resume instead.")
    st.markdown("---")

    url = st.text_input(
        "Public LinkedIn profile URL",
        placeholder="https://www.linkedin.com/in/your-profile/"
    )

    if st.button(" Analyze Profile", disabled=not bool(url)):
        if not api_ok:
            st.error(" API is offline.")
        else:
            with st.spinner("Fetching profile and matching jobs..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/match/linkedin",
                        data={"profile_url": url},
                        timeout=TIMEOUT,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.resume_text = data.get("linkedin_text", "")
                        st.session_state.matches     = data.get("matches", [])
                        st.success("Profile analyzed!")
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Error {resp.status_code}: {detail}")
                except requests.RequestException as e:
                    st.error(f"Connection error: {e}")

    if st.session_state.matches:
        st.markdown("---")
        st.subheader("🎯 Top Matching Jobs")
        render_matches(st.session_state.matches)
elif page == " Paste Resume":
    st.title(" Paste Your Resume Text")
    st.markdown("Copy and paste your resume content below.")
    st.markdown("---")

    pasted = st.text_area(
        "Resume content",
        height=350,
        placeholder="John Doe\nSoftware Engineer\n\nSkills: Python, FastAPI, Machine Learning...\n\nExperience:\n..."
    )

    if st.button(" Analyze Text", disabled=not bool(pasted.strip())):
        if not api_ok:
            st.error(" API is offline.")
        else:
            with st.spinner("Matching jobs..."):
                try:
                    resp = requests.post(
                        f"{API_BASE}/match/paste",
                        data={"text": pasted},
                        timeout=TIMEOUT,
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.resume_text = pasted
                        st.session_state.matches     = data.get("matches", [])
                        st.success("Resume analyzed!")
                    else:
                        detail = resp.json().get("detail", resp.text)
                        st.error(f"Error {resp.status_code}: {detail}")
                except requests.RequestException as e:
                    st.error(f"Connection error: {e}")

    if st.session_state.matches:
        st.markdown("---")
        st.subheader(" Top Matching Jobs")
        render_matches(st.session_state.matches)

elif page == " Top Recommendations":
    st.title(" Top Job Recommendations")
    st.markdown("Get your personalized top-K job recommendations.")
    st.markdown("---")

    if not st.session_state.resume_text:
        st.warning(" No resume loaded yet. Please upload or paste your resume first.")
    else:
        st.info(" Resume loaded. Adjust the slider and click Get Recommendations.")
        top_k = st.slider("Number of recommendations", min_value=1, max_value=20, value=10)

        if st.button(" Get Recommendations"):
            if not api_ok:
                st.error("❌ API is offline.")
            else:
                with st.spinner("Running FAISS recommendation..."):
                    try:
                        resp = requests.post(
                            f"{API_BASE}/recommend/jobs",
                            data={
                                "resume_text": st.session_state.resume_text,
                                "top_k": top_k
                            },
                            timeout=TIMEOUT,
                        )
                        if resp.status_code == 200:
                            recs = resp.json().get("recommendations", [])
                            st.subheader(f"Top {top_k} Recommendations")
                            render_matches(recs)
                        else:
                            detail = resp.json().get("detail", resp.text)
                            st.error(f"Error {resp.status_code}: {detail}")
                    except requests.RequestException as e:
                        st.error(f"Connection error: {e}")

elif page == " Career Chat":
    st.title(" Career Advice Chat")
    st.markdown("Ask career questions based on your resume.")
    st.markdown("---")

    if not st.session_state.resume_text:
        st.warning(" No resume loaded yet. Please upload or paste your resume first.")
    else:
        # Show chat history
        for turn in st.session_state.chat_history:
            with st.chat_message("user"):
                st.write(turn["question"])
            with st.chat_message("assistant"):
                st.write(turn["answer"])

        # Input
        question = st.chat_input("Ask a career question...")

        if question:
            if not api_ok:
                st.error(" API is offline.")
            else:
                with st.chat_message("user"):
                    st.write(question)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        try:
                            resp = requests.post(
                                f"{API_BASE}/chat/ask",
                                data={
                                    "question":    question,
                                    "resume_text": st.session_state.resume_text,
                                },
                                timeout=TIMEOUT,
                            )
                            if resp.status_code == 200:
                                answer = resp.json().get("answer", "")
                                st.write(answer)
                                st.session_state.chat_history.append({
                                    "question": question,
                                    "answer":   answer,
                                })
                            else:
                                detail = resp.json().get("detail", resp.text)
                                st.error(f"Error {resp.status_code}: {detail}")
                        except requests.RequestException as e:
                            st.error(f"Connection error: {e}")

        if st.session_state.chat_history:
            if st.button(" Clear chat"):
                st.session_state.chat_history = []
                st.rerun()
