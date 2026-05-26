from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from auth import get_current_user
from database import SessionLocal, User, UserRole, hash_password

router = APIRouter(prefix="/admin", tags=["admin"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_admin(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user or user.role != UserRole.admin:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Admin only")
    return user


@router.post("/users")
def create_user(
    username: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    surname: str = Form(""),
    role: str = Form("member"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_admin),
):
    username = username.strip().lower()
    if db.query(User).filter(User.username == username).first():
        return RedirectResponse("/controls?error=username_exists", status_code=303)
    try:
        user_role = UserRole(role)
    except ValueError:
        user_role = UserRole.member
    user = User(
        username=username,
        password_hash=hash_password(password),
        name=name.strip(),
        surname=surname.strip(),
        role=user_role,
        gym_id=admin_user.gym_id,
    )
    db.add(user)
    db.commit()
    return RedirectResponse("/controls?success=created", status_code=303)
