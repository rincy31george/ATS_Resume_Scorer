from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from typing import List

from utils.ats_logic import process_resumes, is_valid_resume_file

app = FastAPI()

# Session middleware (admin login)
app.add_middleware(SessionMiddleware, secret_key="secret123")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ---------------- LOGIN ----------------

@app.get("/", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    if username == "admin" and password == "admin123":
        request.session["user"] = "admin"
        return RedirectResponse("/dashboard", status_code=303)

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Invalid credentials"}
    )


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=302)


# ---------------- DASHBOARD ----------------

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    if "user" not in request.session:
        return RedirectResponse("/", status_code=302)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "results": None,
            "top_5": None,
            "error": None
        }
    )


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    jd_text: str = Form(...),
    preferred_skills: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    if "user" not in request.session:
        return RedirectResponse("/", status_code=302)

    # ---------------- VALIDATION ----------------

    # JD validation
    if not jd_text or len(jd_text.strip()) < 30:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "results": None,
                "top_5": None,
                "error": "Job Description must be at least 30 characters long."
            }
        )

    # Resume validation
    valid_resumes = []
    for resume in resumes:
        if not is_valid_resume_file(resume):
            return templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "results": None,
                    "top_5": None,
                    "error": f"Unsupported file type: {resume.filename}. Upload only PDF, DOCX, or TXT."
                }
            )
        valid_resumes.append(resume)

    # ---------------- PROCESSING ----------------

    results = process_resumes(jd_text, valid_resumes, preferred_skills)

    if not results:
        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "results": None,
                "top_5": None,
                "error": "No valid resume content found. Please upload readable files."
            }
        )

    top_5_candidates = results[:5]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "results": results,
            "top_5": top_5_candidates,
            "preferred_skills": preferred_skills,
            "jd_text": jd_text,
            "error": None
        }
    )
