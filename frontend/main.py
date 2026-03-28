import sys
import os
import json

import requests
import streamlit as st
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

API_BASE = "http://127.0.0.1:8000"
TIMEOUT  = 30   # seconds
st.set_page_config(
    page_title="Resume Analyzer & Job Matcher",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
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
    .match-card h4 { margin: 0 0 6px; color: #a5b4fc; font-size: 1rem; }
    .match-card p  { margin: 0; font-size: 0.85rem; color: #94a3b8; }
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
    .chat-bubble-user {
        background: #312e81;
        border-radius: 12px 12px 4px 12px;
        padding: 10px 14px;
        margin: 6px 0;
        color: #e0e7ff;
        max-width: 80%;
        margin-left: auto;
    }
    .chat-bubble-bot {
        background: #1e293b;
        border-radius: 12px 12px 12px 4px;
        border-left: 3px solid #6366f1;
        padding: 10px 14px;
        margin: 6px 0;
        color: #e2e8f0;
        max-width: 85%;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "resume_text"  not in st.session_state: st.session_state.resume_text  = ""
if "matches"      not in st.session_state: st.session_state.matches      = []
if "chat_history" not in st.session_state: st.session_state.chat_history = []

def check_api() -> bool:
    try:
        r = requests.get(f"{API_BASE}/health", timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def render_matches(matches: list):
    if not matches:
        st.info("No matches returned.")
        return
    for m in matches:
        pct = int(m.get("similarity", 0) * 100)
        snippet = m.get("snippet", "")
        st.markdown(f"""
<div class="match-card">
  <h4>#{m.get('rank', '?')}  {m.get('title', 'Unknown Role')}
    <span class="score-pill">{pct}% match</span>
  </h4>
  <p>{snippet}</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("##  Resume Analyzer")
    st.markdown("---")
    page = st.radio(
        "Navigate",
        [" Home", " Upload PDF", " LinkedIn URL", " Paste Resume",
         " Top Recommendations", " Career Chat"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    api_ok = check_api()
    if api_ok:
        st.success(" API connected")
    else:
        st.error(" API offline\nStart: `uvicorn backend.api.main:app --reload`")

    if st.session_state.resume_text:
        st.markdown("---")
        st.caption(" Resume loaded")
        st.caption(st.session_state.resume_text[:120] + "…")

if page == " Home":
    st.title("Resume Analyzer & Job Matcher")
    st.markdown("""
Welcome! This tool helps you:
- **Match your resume** to the most relevant job roles using semantic AI (FAISS + sentence-transformers)
- **Chat** with a career-advice AI (powered by GPT-4o-mini)
- **Get ranked recommendations** for your top-k best-fit jobs

**Get started** → pick an option in the sidebar.
""")
    col1, col2, col3 = st.columns(3)
    col1.metric("Input methods", "3", "PDF / LinkedIn / Paste")
    col2.metric("Matching engine", "FAISS", "Cosine similarity")
    col3.metric("AI advisor", "GPT-4o-mini", "Career Q&A")

elif page == "Upload PDF":
    st.title(" Upload PDF Resume")
    uploaded = st.file_uploader("Choose your PDF resume", type=["pdf"])

    if st.button("Analyze PDF", disabled=not uploaded or not api_ok):
        with st.spinner("Extracting text and matching jobs…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/match/upload",
                    files={"file": (uploaded.name, uploaded.getvalue(), "application/pdf")},
                    timeout=TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.resume_text = data.get("resume_text", "")
                st.session_state.matches     = data.get("matches", [])
                st.success(" Resume analyzed!")
            except requests.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.error(f"API error: {detail}")
            except requests.RequestException as e:
                st.error(f"Connection error: {e}")

    if st.session_state.matches:
        st.subheader(" Top Matching Jobs")
        render_matches(st.session_state.matches)

elif page == " LinkedIn URL":
    st.title(" LinkedIn Profile Matcher")
    st.info(" LinkedIn restricts scraping. Best results on fully public profiles.")
    url = st.text_input("Public LinkedIn profile URL",
                        placeholder="https://www.linkedin.com/in/your-profile/")

    if st.button("Analyze Profile", disabled=not url or not api_ok):
        with st.spinner("Fetching profile and matching jobs…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/match/linkedin",
                    data={"profile_url": url},
                    timeout=TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.resume_text = data.get("linkedin_text", "")
                st.session_state.matches     = data.get("matches", [])
                st.success(" Profile analyzed!")
            except requests.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.error(f"API error: {detail}")
            except requests.RequestException as e:
                st.error(f"Connection error: {e}")

    if st.session_state.matches:
        st.subheader(" Top Matching Jobs")
        render_matches(st.session_state.matches)
elif page == " Paste Resume":
    st.title(" Paste Your Resume Text")
    pasted = st.text_area("Paste resume content here", height=320,
                          placeholder="John Doe\nSoftware Engineer\nSkills: Python, FastAPI, Docker…")

    if st.button("Analyze Text", disabled=not pasted.strip() or not api_ok):
        with st.spinner("Matching jobs…"):
            try:
                resp = requests.post(
                    f"{API_BASE}/match/paste",
                    data={"text": pasted},
                    timeout=TIMEOUT,
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.resume_text = pasted
                st.session_state.matches     = data.get("matches", [])
                st.success("Resume analyzed!")
            except requests.HTTPError as e:
                detail = e.response.json().get("detail", str(e))
                st.error(f"API error: {detail}")
            except requests.RequestException as e:
                st.error(f"Connection error: {e}")

    if st.session_state.matches:
        st.subheader(" Top Matching Jobs")
        render_matches(st.session_state.matches)
elif page == " Top Recommendations":
    st.title(" Top Job Recommendations")

    if not st.session_state.resume_text:
        st.warning("Please upload or paste your resume first (use the sidebar).")
    else:
        top_k = st.slider("Number of recommendations", 1, 20, 10)
        if st.button("Get Recommendations", disabled=not api_ok):
            with st.spinner("Running FAISS recommendation…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/recommend/jobs",
                        data={"resume_text": st.session_state.resume_text, "top_k": top_k},
                        timeout=TIMEOUT,
                    )
                    resp.raise_for_status()
                    recs = resp.json().get("recommendations", [])
                    st.subheader(f"Top {top_k} Recommendations")
                    render_matches(recs)
                except requests.HTTPError as e:
                    detail = e.response.json().get("detail", str(e))
                    st.error(f"API error: {detail}")
                except requests.RequestException as e:
                    st.error(f"Connection error: {e}")

elif page == " Career Chat":
    st.title(" Career Advice Chat")

    if not st.session_state.resume_text:
        st.warning("Please upload or paste your resume first so the AI can personalize advice.")
    else:
        # Render history
        for turn in st.session_state.chat_history:
            st.markdown(f'<div class="chat-bubble-user"> {turn["question"]}</div>',
                        unsafe_allow_html=True)
            st.markdown(f'<div class="chat-bubble-bot"> {turn["answer"]}</div>',
                        unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            question = st.text_input("Ask a career question…",
                                     placeholder="What roles best fit my background?")
            send = st.form_submit_button("Send", disabled=not api_ok)

        if send and question.strip():
            with st.spinner("Thinking…"):
                try:
                    resp = requests.post(
                        f"{API_BASE}/chat/ask",
                        data={
                            "question":    question,
                            "resume_text": st.session_state.resume_text,
                        },
                        timeout=TIMEOUT,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.chat_history.append({
                        "question": question,
                        "answer":   data.get("answer", ""),
                    })
                    st.rerun()
                except requests.HTTPError as e:
                    detail = e.response.json().get("detail", str(e))
                    st.error(f"API error: {detail}")
                except requests.RequestException as e:
                    st.error(f"Connection error: {e}")

        if st.session_state.chat_history:
            if st.button(" Clear chat"):
                st.session_state.chat_history = []
                st.rerun()
