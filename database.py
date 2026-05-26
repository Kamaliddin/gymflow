import enum
import json
from datetime import datetime

from passlib.context import CryptContext
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker

DATABASE_URL = "sqlite:///./gymflow.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

TABLE_COLUMNS = [
    "day_number",
    "exercise_name",
    "set_number",
    "rep_goal",
    "weight",
    "time_per_set",
    "checkbox",
]


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    admin = "admin"
    trainer = "trainer"
    member = "member"


class Gym(Base):
    __tablename__ = "gyms"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, default="GymFlow")

    users = relationship("User", back_populates="gym")
    exercises = relationship("Exercise", back_populates="gym")
    templates = relationship("Template", back_populates="gym")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(80), nullable=False)
    surname = Column(String(80), default="")
    bio = Column(Text, default="")
    profile_pic = Column(String(255), default="")
    role = Column(Enum(UserRole), default=UserRole.member, nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)

    gym = relationship("Gym", back_populates="users")
    member_tables = relationship(
        "WorkoutTable", back_populates="member", foreign_keys="WorkoutTable.member_id"
    )
    trainer_tables = relationship(
        "WorkoutTable", back_populates="trainer", foreign_keys="WorkoutTable.trainer_id"
    )
    exercises_created = relationship("Exercise", back_populates="creator")
    templates = relationship("Template", back_populates="trainer")
    trainer_of = relationship(
        "TrainerMember",
        back_populates="trainer",
        foreign_keys="TrainerMember.trainer_id",
    )
    members_assigned = relationship(
        "TrainerMember",
        back_populates="member",
        foreign_keys="TrainerMember.member_id",
    )

    @property
    def display_name(self):
        parts = [self.name, self.surname] if self.surname else [self.name]
        return " ".join(p for p in parts if p).strip()


class TrainerMember(Base):
    __tablename__ = "trainer_members"

    id = Column(Integer, primary_key=True, index=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    gym_id = Column(Integer, ForeignKey("gyms.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.now)

    trainer = relationship("User", back_populates="trainer_of", foreign_keys=[trainer_id])
    member = relationship("User", back_populates="members_assigned", foreign_keys=[member_id])


class Exercise(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, index=True)
    is_public = Column(Boolean, default=False)
    gym_id = Column(Integer, ForeignKey("gyms.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    gym = relationship("Gym", back_populates="exercises")
    creator = relationship("User", back_populates="exercises_created")
    rows = relationship("TableRow", back_populates="exercise")


class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    gym_id = Column(Integer, ForeignKey("gyms.id"), nullable=True)

    trainer = relationship("User", back_populates="templates")
    gym = relationship("Gym", back_populates="templates")
    tables = relationship("WorkoutTable", back_populates="template_source")


class WorkoutTable(Base):
    __tablename__ = "workout_tables"

    id = Column(Integer, primary_key=True, index=True)
    member_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    trainer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    name = Column(String(120), nullable=False, default="Workout")
    repeat_days = Column(Text, default="[]")
    default_time = Column(String(10), default="08:00")
    template_id = Column(Integer, ForeignKey("templates.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    gym_id = Column(Integer, ForeignKey("gyms.id"), nullable=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)

    member = relationship("User", back_populates="member_tables", foreign_keys=[member_id])
    trainer = relationship("User", back_populates="trainer_tables", foreign_keys=[trainer_id])
    template_source = relationship("Template", back_populates="tables")
    rows = relationship(
        "TableRow", back_populates="table", cascade="all, delete-orphan", order_by="TableRow.id"
    )
    column_permissions = relationship(
        "ColumnPermission", back_populates="table", cascade="all, delete-orphan"
    )

    def get_repeat_days(self):
        try:
            return json.loads(self.repeat_days or "[]")
        except json.JSONDecodeError:
            return []

    def set_repeat_days(self, days):
        self.repeat_days = json.dumps(days)


class TableRow(Base):
    __tablename__ = "table_rows"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("workout_tables.id"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=True)
    exercise_name = Column(String(120), default="")
    day_number = Column(Integer, default=1)
    set_number = Column(Integer, default=1)
    rep_goal = Column(String(40), default="")
    weight = Column(Float, default=0.0)
    time_per_set = Column(String(20), default="")
    checkbox_locked = Column(Boolean, default=False)
    is_checked = Column(Boolean, default=False)

    table = relationship("WorkoutTable", back_populates="rows")
    exercise = relationship("Exercise", back_populates="rows")


class ColumnPermission(Base):
    __tablename__ = "column_permissions"

    id = Column(Integer, primary_key=True, index=True)
    table_id = Column(Integer, ForeignKey("workout_tables.id"), nullable=False)
    column_name = Column(String(40), nullable=False)
    member_can_edit = Column(Boolean, default=True)

    table = relationship("WorkoutTable", back_populates="column_permissions")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def default_column_permissions(table_id: int):
    return [
        ColumnPermission(table_id=table_id, column_name=col, member_can_edit=True)
        for col in TABLE_COLUMNS
    ]


def init_db():
    from seed_demo import is_demo_seeded, seed_demo_data

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not is_demo_seeded(db):
            seed_demo_data(db)
    finally:
        db.close()
