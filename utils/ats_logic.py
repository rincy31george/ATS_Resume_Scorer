from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pdfminer.high_level
from io import BytesIO
import docx

# -----------------------------
# Load NLP Model (Once)
# -----------------------------
model = SentenceTransformer("all-MiniLM-L6-v2")

# -----------------------------
# File Validation
# -----------------------------
ALLOWED_EXTENSIONS = (".pdf", ".docx", ".txt")

def is_valid_resume_file(upload_file):
    if not upload_file or not upload_file.filename:
        return False
    return upload_file.filename.lower().endswith(ALLOWED_EXTENSIONS)

# -----------------------------
# Text Extraction
# -----------------------------
def extract_text_from_pdf(upload_file):
    upload_file.file.seek(0)
    return pdfminer.high_level.extract_text(
        BytesIO(upload_file.file.read())
    ) or ""


def extract_text_from_docx(upload_file):
    upload_file.file.seek(0)
    document = docx.Document(upload_file.file)
    return "\n".join([p.text for p in document.paragraphs]) or ""


def extract_text_from_txt(upload_file):
    upload_file.file.seek(0)
    return upload_file.file.read().decode("utf-8", errors="ignore") or ""


def extract_resume_text(upload_file):
    filename = upload_file.filename.lower()

    try:
        if filename.endswith(".pdf"):
            return extract_text_from_pdf(upload_file)
        elif filename.endswith(".docx"):
            return extract_text_from_docx(upload_file)
        elif filename.endswith(".txt"):
            return extract_text_from_txt(upload_file)
    except Exception:
        return ""

    return ""

# -----------------------------
# Semantic Similarity
# -----------------------------
def calculate_semantic_score(jd_text, resume_text):
    jd_emb = model.encode([jd_text])
    resume_emb = model.encode([resume_text])
    similarity = cosine_similarity(jd_emb, resume_emb)[0][0]
    return similarity * 100

# -----------------------------
# Preferred Skill Matching
# -----------------------------
def match_skills(preferred_skills, resume_text):
    if not preferred_skills.strip():
        return [], []

    preferred = [s.strip().lower() for s in preferred_skills.split(",")]
    resume_text = resume_text.lower()

    matched = []
    not_matched = []

    for skill in preferred:
        if skill and skill in resume_text:
            matched.append(skill)
        else:
            not_matched.append(skill)

    return matched, not_matched

# -----------------------------
# ATS Score Logic
# -----------------------------
def calculate_final_ats_score(semantic_score, matched, total_skills):
    semantic_component = (semantic_score / 100) * 60

    if total_skills > 0:
        skill_component = (len(matched) / total_skills) * 30
    else:
        skill_component = 0

    final_score = semantic_component + skill_component
    return round(final_score, 2), round(semantic_component, 2), round(skill_component, 2)

# -----------------------------
# Main Processing
# -----------------------------
def process_resumes(jd_text, resumes, preferred_skills):
    results = []
    total_skills = len([s for s in preferred_skills.split(",") if s.strip()])

    for resume in resumes:
        resume_text = extract_resume_text(resume)

        # Skip empty/unreadable resumes
        if not resume_text or len(resume_text.strip()) < 20:
            continue

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

    # Sort DESC
    results.sort(key=lambda x: x["ats_score"], reverse=True)

    return results
