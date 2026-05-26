import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import get_current_user, require_user
from database import (
    TABLE_COLUMNS,
    ColumnPermission,
    Exercise,
    SessionLocal,
    TableRow,
    Template,
    TrainerMember,
    User,
    UserRole,
    WorkoutTable,
    default_column_permissions,
)

router = APIRouter(prefix="/api", tags=["api"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def can_access_member(user: User, member_id: int, db: Session) -> bool:
    if user.id == member_id:
        return True
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.trainer:
        link = (
            db.query(TrainerMember)
            .filter(TrainerMember.trainer_id == user.id, TrainerMember.member_id == member_id)
            .first()
        )
        return link is not None
    return False


def can_edit_table(user: User, table: WorkoutTable, db: Session) -> bool:
    if user.role == UserRole.admin:
        return True
    if user.role == UserRole.trainer:
        return table.trainer_id == user.id or can_access_member(user, table.member_id, db)
    if user.role == UserRole.member:
        return table.member_id == user.id
    return False


def is_trainer_or_admin(user: User) -> bool:
    return user.role in (UserRole.trainer, UserRole.admin)


def row_to_dict(row: TableRow, perms: dict) -> dict:
    return {
        "id": row.id,
        "table_id": row.table_id,
        "exercise_id": row.exercise_id,
        "exercise_name": row.exercise_name or (row.exercise.name if row.exercise else ""),
        "day_number": row.day_number,
        "set_number": row.set_number,
        "rep_goal": row.rep_goal,
        "weight": row.weight,
        "time_per_set": row.time_per_set,
        "checkbox_locked": row.checkbox_locked,
        "is_checked": row.is_checked,
        "permissions": perms,
    }


def table_to_dict(table: WorkoutTable, user: User) -> dict:
    perms = {p.column_name: p.member_can_edit for p in table.column_permissions}
    if not perms:
        perms = {c: True for c in TABLE_COLUMNS}
    rows = [row_to_dict(r, perms) for r in table.rows]
    return {
        "id": table.id,
        "member_id": table.member_id,
        "trainer_id": table.trainer_id,
        "name": table.name,
        "repeat_days": table.get_repeat_days(),
        "default_time": table.default_time,
        "template_id": table.template_id,
        "is_public": table.is_public,
        "sort_order": table.sort_order,
        "column_permissions": perms,
        "rows": rows,
        "can_edit_all": is_trainer_or_admin(user),
        "is_trainer_view": user.role in (UserRole.trainer, UserRole.admin)
        and user.id != table.member_id,
    }


class TableCreate(BaseModel):
    member_id: Optional[int] = None
    name: str = "Workout"
    repeat_days: list[int] = []
    default_time: str = "08:00"
    template_id: Optional[int] = None


class TableUpdate(BaseModel):
    name: Optional[str] = None
    repeat_days: Optional[list[int]] = None
    default_time: Optional[str] = None


class RowCreate(BaseModel):
    table_id: int
    exercise_id: Optional[int] = None
    exercise_name: str = ""
    day_number: int = 1
    set_number: int = 1
    rep_goal: str = ""
    weight: float = 0
    time_per_set: str = ""
    checkbox_locked: bool = False
    is_checked: bool = False


class RowUpdate(BaseModel):
    exercise_id: Optional[int] = None
    exercise_name: Optional[str] = None
    day_number: Optional[int] = None
    set_number: Optional[int] = None
    rep_goal: Optional[str] = None
    weight: Optional[float] = None
    time_per_set: Optional[str] = None
    checkbox_locked: Optional[bool] = None
    is_checked: Optional[bool] = None


class PermissionUpdate(BaseModel):
    column_name: str
    member_can_edit: bool


@router.get("/exercises")
def search_exercises(
    request: Request,
    q: str = "",
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    query = db.query(Exercise)
    gym_id = user.gym_id
    if gym_id:
        query = query.filter(
            (Exercise.gym_id == gym_id) | (Exercise.is_public == True)  # noqa: E712
        )
    if q:
        query = query.filter(Exercise.name.ilike(f"%{q}%"))
    exercises = query.order_by(Exercise.name).limit(30).all()
    return [{"id": e.id, "name": e.name} for e in exercises]


@router.post("/exercises")
def create_exercise(
    request: Request,
    body: dict,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    name = (body.get("name") or "").strip()
    if not name:
        raise HTTPException(400, "Name required")
    existing = db.query(Exercise).filter(Exercise.name == name, Exercise.gym_id == user.gym_id).first()
    if existing:
        return {"id": existing.id, "name": existing.name}
    ex = Exercise(name=name, is_public=False, gym_id=user.gym_id, creator_id=user.id)
    db.add(ex)
    db.commit()
    db.refresh(ex)
    return {"id": ex.id, "name": ex.name}


@router.get("/plan")
def get_plan_data(
    request: Request,
    member_id: Optional[int] = None,
    day: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    target_id = member_id or user.id
    if not can_access_member(user, target_id, db):
        raise HTTPException(403, "Access denied")

    tables = (
        db.query(WorkoutTable)
        .filter(WorkoutTable.member_id == target_id)
        .order_by(WorkoutTable.sort_order, WorkoutTable.id)
        .all()
    )
    day_tables = []
    if day is not None:
        for t in tables:
            days = t.get_repeat_days()
            if not days or day in days:
                day_tables.append(t)
        day_tables = day_tables[:3]
    else:
        day_tables = tables

    templates_q = db.query(Template)
    if user.gym_id:
        templates_q = templates_q.filter(
            (Template.gym_id == user.gym_id)
            & (
                (Template.is_public == True)  # noqa: E712
                | (Template.trainer_id == user.id)
                | (user.role == UserRole.admin)
            )
        )
    templates = templates_q.all() if user.role != UserRole.member else []

    member = db.query(User).filter(User.id == target_id).first()

    return {
        "member": {
            "id": member.id,
            "name": member.display_name,
            "username": member.username,
        }
        if member
        else None,
        "tables": [table_to_dict(t, user) for t in (day_tables if day is not None else tables)],
        "all_tables": [table_to_dict(t, user) for t in tables],
        "templates": [
            {"id": t.id, "name": t.name, "is_public": t.is_public, "trainer_id": t.trainer_id}
            for t in templates
        ],
        "viewer_role": user.role.value,
        "max_tables_per_day": 3,
    }


@router.post("/tables")
def create_table(
    body: TableCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    member_id = body.member_id or user.id
    if not can_access_member(user, member_id, db):
        raise HTTPException(403, "Access denied")
    if user.role == UserRole.member and member_id != user.id:
        raise HTTPException(403, "Members can only create own tables")

    count = db.query(WorkoutTable).filter(WorkoutTable.member_id == member_id).count()
    if count >= 21:
        raise HTTPException(400, "Table limit reached")

    trainer_id = user.id if user.role == UserRole.trainer else None
    if user.role == UserRole.admin:
        link = db.query(TrainerMember).filter(TrainerMember.member_id == member_id).first()
        trainer_id = link.trainer_id if link else user.id

    table = WorkoutTable(
        member_id=member_id,
        trainer_id=trainer_id,
        name=body.name,
        default_time=body.default_time,
        template_id=body.template_id,
        gym_id=user.gym_id,
        sort_order=count,
    )
    table.set_repeat_days(body.repeat_days)
    db.add(table)
    db.flush()
    db.add_all(default_column_permissions(table.id))
    db.commit()
    db.refresh(table)
    return table_to_dict(table, user)


@router.patch("/tables/{table_id}")
def update_table(
    table_id: int,
    body: TableUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    table = db.query(WorkoutTable).filter(WorkoutTable.id == table_id).first()
    if not table:
        raise HTTPException(404, "Table not found")
    if not can_edit_table(user, table, db):
        raise HTTPException(403, "Access denied")

    if body.name is not None:
        table.name = body.name
    if body.repeat_days is not None:
        table.set_repeat_days(body.repeat_days)
    if body.default_time is not None:
        table.default_time = body.default_time
    db.commit()
    db.refresh(table)
    return table_to_dict(table, user)


@router.delete("/tables/{table_id}")
def delete_table(
    table_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    table = db.query(WorkoutTable).filter(WorkoutTable.id == table_id).first()
    if not table:
        raise HTTPException(404, "Table not found")
    if not can_edit_table(user, table, db):
        raise HTTPException(403, "Access denied")
    db.delete(table)
    db.commit()
    return {"ok": True}


@router.post("/tables/{table_id}/rows")
def add_row(
    table_id: int,
    body: RowCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    table = db.query(WorkoutTable).filter(WorkoutTable.id == table_id).first()
    if not table:
        raise HTTPException(404, "Table not found")
    if not can_edit_table(user, table, db):
        raise HTTPException(403, "Access denied")

    row = TableRow(
        table_id=table_id,
        exercise_id=body.exercise_id,
        exercise_name=body.exercise_name,
        day_number=body.day_number,
        set_number=body.set_number,
        rep_goal=body.rep_goal,
        weight=body.weight,
        time_per_set=body.time_per_set,
        checkbox_locked=body.checkbox_locked if is_trainer_or_admin(user) else False,
        is_checked=body.is_checked,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    perms = {p.column_name: p.member_can_edit for p in table.column_permissions}
    return row_to_dict(row, perms)


@router.patch("/rows/{row_id}")
def update_row(
    row_id: int,
    body: RowUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    row = db.query(TableRow).filter(TableRow.id == row_id).first()
    if not row:
        raise HTTPException(404, "Row not found")
    table = row.table
    if not can_edit_table(user, table, db):
        raise HTTPException(403, "Access denied")

    perms = {p.column_name: p.member_can_edit for p in table.column_permissions}
    data = body.model_dump(exclude_unset=True)

    if user.role == UserRole.member:
        for field in data:
            col = field if field != "is_checked" else "checkbox"
            if field == "checkbox_locked":
                raise HTTPException(403, "Cannot lock checkbox")
            if col in perms and not perms.get(col, True):
                raise HTTPException(403, f"Column {col} is locked")
        if "is_checked" in data and row.checkbox_locked and not perms.get("checkbox", True):
            raise HTTPException(403, "Checkbox locked")

    if "checkbox_locked" in data and not is_trainer_or_admin(user):
        del data["checkbox_locked"]

    for k, v in data.items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row_to_dict(row, perms)


@router.delete("/rows/{row_id}")
def delete_row(
    row_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    row = db.query(TableRow).filter(TableRow.id == row_id).first()
    if not row:
        raise HTTPException(404, "Row not found")
    table = row.table
    if not can_edit_table(user, table, db):
        raise HTTPException(403, "Access denied")
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.patch("/tables/{table_id}/permissions")
def update_permission(
    table_id: int,
    body: PermissionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_user),
):
    if not is_trainer_or_admin(user):
        raise HTTPException(403, "Trainers only")
    table = db.query(WorkoutTable).filter(WorkoutTable.id == table_id).first()
    if not table:
        raise HTTPException(404, "Table not found")
    if body.column_name not in TABLE_COLUMNS:
        raise HTTPException(400, "Invalid column")

    perm = (
        db.query(ColumnPermission)
        .filter(
            ColumnPermission.table_id == table_id,
            ColumnPermission.column_name == body.column_name,
        )
        .first()
    )
    if not perm:
        perm = ColumnPermission(
            table_id=table_id,
            column_name=body.column_name,
            member_can_edit=body.member_can_edit,
        )
        db.add(perm)
    else:
        perm.member_can_edit = body.member_can_edit
    db.commit()
    return {"column_name": body.column_name, "member_can_edit": body.member_can_edit}

