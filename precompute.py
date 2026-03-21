import pickle
from sentence_transformers import SentenceTransformer
from resume_data_loader import load_resumes

print("Loading resumes...")
resumes = load_resumes()

texts = [r["content"] for r in resumes]
names = [r["filename"] for r in resumes]

print("Loading model...")
model = SentenceTransformer("all-MiniLM-L6-v2")

print("Computing embeddings...")
embeddings = model.encode(texts, batch_size=32, show_progress_bar=True)

with open("embeddings.pkl", "wb") as f:
    pickle.dump((names, texts, embeddings), f)

print("✅ Embeddings saved to embeddings.pkl")