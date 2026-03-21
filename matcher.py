from sklearn.metrics.pairwise import cosine_similarity


class ResumeMatcher:
    def __init__(self, model):
        self.model = model

    def rank_resumes(self, names, embeddings, job_text):
        job_embedding = self.model.encode([job_text])[0]

        similarities = cosine_similarity([job_embedding], embeddings)[0]

        results = list(zip(names, similarities))
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def match_single_resume(self, resume_text, job_text):
        resume_emb = self.model.encode([resume_text])[0]
        job_emb = self.model.encode([job_text])[0]

        score = cosine_similarity([resume_emb], [job_emb])[0][0]

        return float(score)