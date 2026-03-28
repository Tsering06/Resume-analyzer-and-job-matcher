import os
import pickle
import numpy as np

import faiss
from sentence_transformers import SentenceTransformer

from backend.resume_data_loader import load_jobs

EMBEDDINGS_DIR = os.path.join(os.path.dirname(__file__), "embeddings")
EMB_PATH       = os.path.join(EMBEDDINGS_DIR, "job_embeddings.pkl")
TITLES_PATH    = os.path.join(EMBEDDINGS_DIR, "job_titles.pkl")
TEXTS_PATH     = os.path.join(EMBEDDINGS_DIR, "job_texts.pkl")


class FAISSMatcher:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        print("🔄 Loading sentence-transformer model…")
        self.model = SentenceTransformer(model_name)
        self.index      = None
        self.job_texts  = []
        self.job_titles = []
        self.embeddings = None

        os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
        self._load_or_build()

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _load_or_build(self):
        if os.path.exists(EMB_PATH) and os.path.exists(TITLES_PATH):
            try:
                self._load_precomputed()
                return
            except Exception as e:
                print(f"⚠️  Precomputed embeddings corrupt ({e}), rebuilding…")
        self._build_embeddings()

    def _load_precomputed(self):
        print("⚡ Loading precomputed FAISS embeddings…")
        with open(EMB_PATH,    "rb") as f: self.embeddings  = pickle.load(f)
        with open(TITLES_PATH, "rb") as f: self.job_titles  = pickle.load(f)
        with open(TEXTS_PATH,  "rb") as f: self.job_texts   = pickle.load(f)
        self._build_index()
        print(f"✅ Loaded {len(self.job_titles)} jobs from cache.")

    def _build_embeddings(self):
        print("🏗️  Building FAISS index from job dataset…")
        self.job_texts, self.job_titles = load_jobs()
        if not self.job_texts:
            raise RuntimeError("No jobs loaded — check Dataset/jobs/jobdataset.csv")

        self.embeddings = self.model.encode(
            self.job_texts, convert_to_numpy=True, show_progress_bar=True
        )
        self._build_index()

        with open(EMB_PATH,    "wb") as f: pickle.dump(self.embeddings,  f)
        with open(TITLES_PATH, "wb") as f: pickle.dump(self.job_titles,  f)
        with open(TEXTS_PATH,  "wb") as f: pickle.dump(self.job_texts,   f)
        print(f"✅ Built and cached embeddings for {len(self.job_titles)} jobs.")

    def _build_index(self):
        # Normalise embeddings → use inner-product as cosine similarity
        emb = self.embeddings.astype(np.float32).copy()
        faiss.normalize_L2(emb)
        self.index = faiss.IndexFlatIP(emb.shape[1])   # IP = cosine after L2-norm
        self.index.add(emb)

    # ── Public API ────────────────────────────────────────────────────────────

    def recommend_jobs(self, resume_text: str, top_k: int = 5):
        """
        Return top-k matching jobs.
        Each result: {"rank": int, "title": str, "similarity": float (0-1),
                      "snippet": str}
        """
        query = self.model.encode([resume_text], convert_to_numpy=True).astype(np.float32)
        faiss.normalize_L2(query)
        scores, indices = self.index.search(query, min(top_k, len(self.job_titles)))

        results = []
        for rank, (idx, score) in enumerate(zip(indices[0], scores[0]), start=1):
            if idx == -1:
                continue
            results.append({
                "rank":       rank,
                "title":      self.job_titles[idx],
                "similarity": round(float(score), 4),   # 1.0 = perfect match
                "snippet":    self.job_texts[idx][:200].strip() + "…",
            })
        return results

    def match_resume(self, resume_text: str, top_k: int = 5):
        """Alias kept for route compatibility."""
        return self.recommend_jobs(resume_text, top_k=top_k)


# ── Singleton (imported by routes) ───────────────────────────────────────────
matcher = FAISSMatcher()
