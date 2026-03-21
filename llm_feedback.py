from transformers import pipeline
import json

class ResumeFeedbackGenerator:
    def __init__(self):
        """
        Initialize the instruction-tuned model pipeline.
        'google/flan-t5-large' is instruction-tuned and suitable for resume analysis.
        """
        self.generator = pipeline(
            "text-generation",
            model="google/flan-t5-large",
            device=0  # use GPU if available, remove or set -1 for CPU
        )

    def generate_feedback(self, resume_text: str, job_text: str) -> dict:
        """
        Generate structured feedback comparing resume against the job description.
        Returns a JSON-like dictionary with Strengths, Gaps, and Suggestions.
        """
        resume_excerpt = resume_text[:1500]  # truncate long resumes
        job_excerpt = job_text[:1000]        # truncate long job descriptions

        prompt = f"""
You are a senior HR recruiter and career coach. 
Analyze the following resume against the given job description. 
Provide personalized feedback in JSON format.

Instructions:
1. List strengths that match the job requirements.
2. Identify missing skills or gaps relevant to the job.
3. Provide actionable suggestions to improve the resume for this job.

Output format (JSON):
{{
  "Strengths": ["..."],
  "Gaps": ["..."],
  "Suggestions": ["..."]
}}

Resume:
{resume_excerpt}

Job Description:
{job_excerpt}
"""

        output = self.generator(
            prompt,
            max_new_tokens=400,
            do_sample=True,       # enable dynamic, non-repetitive outputs
            temperature=0.7
        )

        text_output = output[0]['generated_text'].strip()

        # Attempt to parse JSON output
        try:
            feedback_json = json.loads(text_output)
        except json.JSONDecodeError:
            # Fallback: return text in raw format if JSON parsing fails
            feedback_json = {
                "Strengths": [],
                "Gaps": [],
                "Suggestions": [],
                "Raw": text_output
            }

        return feedback_json

    def skill_gap_analysis(self, resume_text: str, job_text: str) -> dict:
        """
        Identify missing skills between resume and job description.
        Returns a JSON-like dictionary with Missing_Skills list.
        """
        resume_excerpt = resume_text[:1500]
        job_excerpt = job_text[:1000]

        prompt = f"""
You are a senior HR recruiter.

Compare the resume to the job description and identify ONLY the missing skills.
Return the output as JSON:

{{
  "Missing_Skills": ["..."]
}}

Resume:
{resume_excerpt}

Job Description:
{job_excerpt}
"""

        output = self.generator(
            prompt,
            max_new_tokens=200,
            do_sample=True,
            temperature=0.7
        )

        text_output = output[0]['generated_text'].strip()

        try:
            skills_json = json.loads(text_output)
        except json.JSONDecodeError:
            skills_json = {
                "Missing_Skills": [],
                "Raw": text_output
            }

        return skills_json


# Global instance for easy access
feedback_generator = ResumeFeedbackGenerator()


# Top-level functions for import
def generate_feedback(resume_text: str, job_text: str) -> dict:
    return feedback_generator.generate_feedback(resume_text, job_text)

def skill_gap_analysis(resume_text: str, job_text: str) -> dict:
    return feedback_generator.skill_gap_analysis(resume_text, job_text)