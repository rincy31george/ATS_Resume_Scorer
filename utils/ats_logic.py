from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pdfminer.high_level
from io import BytesIO

# -----------------------------
# Load NLP Model (Once)
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# PDF Text Extraction
# -----------------------------
def extract_text_from_pdf(upload_file):
    """
    Extract text safely from uploaded PDF file
    """
    upload_file.file.seek(0)
    return pdfminer.high_level.extract_text(
        BytesIO(upload_file.file.read())
    )

# -----------------------------
# Semantic Similarity Score
# -----------------------------
def calculate_semantic_score(jd_text, resume_text):
    """
    Calculates semantic similarity using Sentence Transformers
    Returns percentage score (0–100)
    """
    jd_emb = model.encode([jd_text])
    resume_emb = model.encode([resume_text])
    similarity = cosine_similarity(jd_emb, resume_emb)[0][0]
    return similarity * 100

# -----------------------------
# Preferred Skill Matching
# -----------------------------
def match_skills(preferred_skills, resume_text):
    """
    Matches recruiter-defined skills against resume text
    """
    if not preferred_skills.strip():
        return [], []

    preferred = [s.strip().lower() for s in preferred_skills.split(",")]
    resume_text = resume_text.lower()

    matched = []
    not_matched = []

    for skill in preferred:
        if skill in resume_text:
            matched.append(skill)
        else:
            not_matched.append(skill)

    return matched, not_matched

# -----------------------------
# ATS Scoring Logic
# -----------------------------
def calculate_final_ats_score(semantic_score, matched, total_skills):
    """
    ATS Score Breakdown:
    - 60% Semantic Similarity
    - 30% Preferred Skill Match
    - 10% Reserved for future enhancements
    """

    semantic_component = (semantic_score / 100) * 60

    if total_skills > 0:
        skill_component = (len(matched) / total_skills) * 30
    else:
        skill_component = 0

    final_score = semantic_component + skill_component
    return round(final_score, 2), round(semantic_component, 2), round(skill_component, 2)

# -----------------------------
# Main Resume Processing
# -----------------------------
def process_resumes(jd_file, resumes, preferred_skills):
    """
    Process N resumes against 1 JD
    Returns sorted ATS results
    """

    # Read JD text safely
    jd_file.file.seek(0)
    jd_text = pdfminer.high_level.extract_text(
        BytesIO(jd_file.file.read())
    )

    results = []
    total_skills = len([s for s in preferred_skills.split(",") if s.strip()])

    for resume in resumes:
        resume_text = extract_text_from_pdf(resume)

        semantic_score = calculate_semantic_score(jd_text, resume_text)
        matched, not_matched = match_skills(preferred_skills, resume_text)

        final_ats, semantic_part, skill_part = calculate_final_ats_score(
            semantic_score,
            matched,
            total_skills
        )

        results.append({
            "filename": resume.filename,
            "ats_score": final_ats,
            "semantic_score": semantic_part,
            "skill_score": skill_part,
            "matched_skills": matched,
            "not_matched_skills": not_matched
        })

    # Sort candidates by ATS score (Descending)
    results.sort(key=lambda x: x["ats_score"], reverse=True)

    return results
