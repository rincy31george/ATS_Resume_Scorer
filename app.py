from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from typing import List



from utils.ats_logic import process_resumes

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

    return templates.TemplateResponse("dashboard.html", {"request": request, "results": None, "top_5": None})


@app.post("/analyze", response_class=HTMLResponse)
async def analyze(
    request: Request,
    jd_file: UploadFile = File(...),
    preferred_skills: str = Form(...),
    resumes: List[UploadFile] = File(...)
):
    if "user" not in request.session:
        return RedirectResponse("/", status_code=302)

    # Process all resumes (sorted DESC)
    results = process_resumes(jd_file, resumes, preferred_skills)

    # Extract Top 5 candidates
    top_5_candidates = results[:5]

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "results": results,          # ALL candidates
            "top_5": top_5_candidates,   # ONLY top 5
            "preferred_skills": preferred_skills
        }
    )
