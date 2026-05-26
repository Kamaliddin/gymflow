from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

import admin
import api
from auth import SECRET_KEY, get_current_user, set_auth_session
from database import (
    SessionLocal,
    TrainerMember,
    User,
    UserRole,
    init_db,
    verify_password,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="GymFlow", lifespan=lifespan)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

templates = Jinja2Templates(directory="templates")
app.state.templates = templates

app.include_router(admin.router)
app.include_router(api.router)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    redirect = "/plan"
    if user:
        if user.role == UserRole.trainer:
            redirect = "/members"
        elif user.role == UserRole.admin:
            redirect = "/controls"
    return templates.TemplateResponse(
        request,
        "home.html",
        {"page_title": "Home", "active_page": "home", "user": user},
    )


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/plan", status_code=303)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"page_title": "Login", "active_page": "login", "error": request.query_params.get("error")},
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse("/login?error=invalid", status_code=303)
    token = set_auth_session(request, user)
    response = RedirectResponse(
        "/members" if user.role == UserRole.trainer else "/controls" if user.role == UserRole.admin else "/plan",
        status_code=303,
    )
    response.set_cookie("access_token", token, httponly=True, max_age=60 * 60 * 24 * 7)
    return response


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.get("/plan", response_class=HTMLResponse)
def plan_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    member_id = request.query_params.get("member_id")
    day = request.query_params.get("day")
    target_member = None
    if member_id and user:
        mid = int(member_id)
        if user.role in (UserRole.trainer, UserRole.admin) or user.id == mid:
            target_member = db.query(User).filter(User.id == mid).first()
    elif user and user.role == UserRole.member:
        target_member = user

    return templates.TemplateResponse(
        request,
        "plan.html",
        {
            "page_title": "Workout Plan",
            "active_page": "plan",
            "user": user,
            "target_member": target_member,
            "day_filter": int(day) if day and day.isdigit() else None,
        },
    )


@app.get("/members", response_class=HTMLResponse)
def members_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role not in (UserRole.trainer, UserRole.admin):
        return RedirectResponse("/login?error=unauthorized", status_code=303)

    if user.role == UserRole.trainer:
        links = db.query(TrainerMember).filter(TrainerMember.trainer_id == user.id).all()
        member_ids = [l.member_id for l in links]
        members = db.query(User).filter(User.id.in_(member_ids)).all() if member_ids else []
    else:
        members = db.query(User).filter(User.role == UserRole.member).all()

    return templates.TemplateResponse(
        request,
        "members.html",
        {
            "page_title": "Members",
            "active_page": "members",
            "user": user,
            "members": members,
        },
    )


@app.post("/members/add")
def add_member(
    request: Request,
    username: str = Form(...),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user or user.role not in (UserRole.trainer, UserRole.admin):
        return RedirectResponse("/login?error=unauthorized", status_code=303)
    member = db.query(User).filter(User.username == username.strip().lower()).first()
    if not member or member.role != UserRole.member:
        return RedirectResponse("/members?error=not_found", status_code=303)
    existing = (
        db.query(TrainerMember)
        .filter(TrainerMember.trainer_id == user.id, TrainerMember.member_id == member.id)
        .first()
    )
    if not existing:
        db.add(
            TrainerMember(
                trainer_id=user.id, member_id=member.id, gym_id=user.gym_id or 1
            )
        )
        db.commit()
    return RedirectResponse("/members?success=added", status_code=303)


@app.get("/calendar", response_class=HTMLResponse)
def calendar_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(
        request,
        "calendar.html",
        {"page_title": "Calendar", "active_page": "calendar", "user": user},
    )


@app.get("/controls", response_class=HTMLResponse)
def controls_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != UserRole.admin:
        return RedirectResponse("/login?error=unauthorized", status_code=303)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "controls.html",
        {
            "page_title": "Admin Controls",
            "active_page": "controls",
            "user": user,
            "users": users,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )


@app.get("/about", response_class=HTMLResponse)
def about_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(
        request,
        "about.html",
        {"page_title": "About", "active_page": "about", "user": user},
    )


@app.get("/api/me")
def api_me(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse({"user": None}, status_code=401)
    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "surname": user.surname,
            "bio": user.bio,
            "profile_pic": user.profile_pic,
            "role": user.role.value,
            "display_name": user.display_name,
        }
    }


@app.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?error=unauthorized", status_code=303)
    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "page_title": "Profile",
            "active_page": "",
            "user": user,
            "success": request.query_params.get("success"),
            "error": request.query_params.get("error"),
        },
    )


@app.post("/profile")
def profile_update(
    request: Request,
    name: str = Form(...),
    surname: str = Form(""),
    bio: str = Form(""),
    profile_pic_url: str = Form(""),
    profile_pic_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login?error=unauthorized", status_code=303)

    # Update basic fields
    user.name = name.strip() if name else user.name
    user.surname = surname.strip() if surname else user.surname
    user.bio = bio or ""

    # Handle uploaded file
    if profile_pic_file is not None and profile_pic_file.filename:
        import os
        from datetime import datetime

        ext = os.path.splitext(profile_pic_file.filename)[1]
        safe_name = f"user_{user.id}_{int(datetime.utcnow().timestamp())}{ext}"
        dest_path = os.path.join("uploads", safe_name)
        with open(dest_path, "wb") as f:
            f.write(profile_pic_file.file.read())
        user.profile_pic = f"/uploads/{safe_name}"
    elif profile_pic_url:
        user.profile_pic = profile_pic_url.strip()

    db.add(user)
    db.commit()
    return RedirectResponse("/profile?success=ok", status_code=303)
