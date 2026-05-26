"""Demo dataset for GymFlow — run via init_db() on fresh database."""

from database import (
    TABLE_COLUMNS,
    ColumnPermission,
    Exercise,
    Gym,
    TableRow,
    Template,
    TrainerMember,
    User,
    UserRole,
    WorkoutTable,
    default_column_permissions,
    hash_password,
)

DEMO_GYM_NAME = "Iron Forge Gym"
DEFAULT_PASSWORD = "demo123"


def is_demo_seeded(db) -> bool:
    return db.query(Gym).filter(Gym.name == DEMO_GYM_NAME).first() is not None


def _user(db, username, name, surname, role, gym_id, bio=""):
    u = User(
        username=username,
        password_hash=hash_password(DEFAULT_PASSWORD),
        name=name,
        surname=surname,
        bio=bio,
        role=role,
        gym_id=gym_id,
    )
    db.add(u)
    db.flush()
    return u


def _exercise(db, name, gym_id, creator_id=None, public=True):
    ex = Exercise(name=name, is_public=public, gym_id=gym_id, creator_id=creator_id)
    db.add(ex)
    db.flush()
    return ex


def _template(db, name, gym_id, trainer_id, public=True):
    t = Template(name=name, gym_id=gym_id, trainer_id=trainer_id, is_public=public)
    db.add(t)
    db.flush()
    return t


def _link(db, trainer_id, member_id, gym_id):
    db.add(TrainerMember(trainer_id=trainer_id, member_id=member_id, gym_id=gym_id))


def _table(db, member, trainer, name, days, time, gym_id, template_id=None, sort_order=0):
    t = WorkoutTable(
        member_id=member.id,
        trainer_id=trainer.id,
        name=name,
        default_time=time,
        template_id=template_id,
        gym_id=gym_id,
        sort_order=sort_order,
    )
    t.set_repeat_days(days)
    db.add(t)
    db.flush()
    db.add_all(default_column_permissions(t.id))
    if name in ("Chest Day", "Leg Day"):
        perm = (
            db.query(ColumnPermission)
            .filter(
                ColumnPermission.table_id == t.id,
                ColumnPermission.column_name == "weight",
            )
            .first()
        )
        if perm:
            perm.member_can_edit = False
    return t


def _rows(db, table, exercise_map, specs):
    """specs: list of dicts with exercise, set, reps, weight, day, time, checked, locked."""
    for s in specs:
        name = s["exercise"]
        db.add(
            TableRow(
                table_id=table.id,
                exercise_id=exercise_map.get(name),
                exercise_name=name,
                day_number=s.get("day", 1),
                set_number=s["set"],
                rep_goal=str(s["reps"]),
                weight=float(s.get("weight", 0)),
                time_per_set=s.get("time", ""),
                is_checked=s.get("checked", False),
                checkbox_locked=s.get("locked", False),
            )
        )


def seed_demo_data(db):
    if is_demo_seeded(db):
        return

    gym = Gym(name=DEMO_GYM_NAME)
    db.add(gym)
    db.flush()

    admin = _user(db, "admin", "Morgan", "Reed", UserRole.admin, gym.id, "Gym owner")
    trainer1 = _user(
        db, "alex_coach", "Alex", "Stone", UserRole.trainer, gym.id, "Strength & hypertrophy"
    )
    trainer2 = _user(
        db, "sam_trainer", "Sam", "Rivera", UserRole.trainer, gym.id, "Athletic performance"
    )

    members = [
        _user(db, "jordan", "Jordan", "Lee", UserRole.member, gym.id),
        _user(db, "taylor", "Taylor", "Kim", UserRole.member, gym.id),
        _user(db, "casey", "Casey", "Brooks", UserRole.member, gym.id),
        _user(db, "riley", "Riley", "Nguyen", UserRole.member, gym.id),
    ]

    exercise_names = [
        "Bench Press",
        "Incline Dumbbell Press",
        "Cable Fly",
        "Push-up",
        "Overhead Press",
        "Lateral Raise",
        "Tricep Pushdown",
        "Dip",
        "Barbell Squat",
        "Romanian Deadlift",
        "Leg Press",
        "Walking Lunge",
        "Calf Raise",
        "Pull-up",
        "Barbell Row",
        "Lat Pulldown",
        "Face Pull",
        "Plank",
        "Hip Thrust",
        "Bulgarian Split Squat",
    ]
    exercise_map = {n: _exercise(db, n, gym.id).id for n in exercise_names}

    tpl_chest = _template(db, "Chest Day", gym.id, trainer1.id, public=True)
    tpl_push = _template(db, "Push Day", gym.id, trainer1.id, public=True)
    tpl_leg = _template(db, "Leg Day", gym.id, trainer2.id, public=True)

    _link(db, trainer1.id, members[0].id, gym.id)
    _link(db, trainer1.id, members[1].id, gym.id)
    _link(db, trainer2.id, members[2].id, gym.id)
    _link(db, trainer2.id, members[3].id, gym.id)

    # Jordan — chest-focused (Alex)
    t = _table(db, members[0], trainer1, "Chest Day", [1, 4], "07:30", gym.id, tpl_chest.id, 0)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Bench Press", "set": 1, "reps": 8, "weight": 80, "time": "2:00"},
            {"exercise": "Bench Press", "set": 2, "reps": 8, "weight": 80, "time": "2:00"},
            {"exercise": "Bench Press", "set": 3, "reps": 8, "weight": 77.5, "time": "2:15"},
            {"exercise": "Bench Press", "set": 4, "reps": 8, "weight": 77.5, "time": "2:15", "checked": True},
            {"exercise": "Incline Dumbbell Press", "set": 1, "reps": 10, "weight": 28},
            {"exercise": "Incline Dumbbell Press", "set": 2, "reps": 10, "weight": 28},
            {"exercise": "Incline Dumbbell Press", "set": 3, "reps": 10, "weight": 26},
            {"exercise": "Cable Fly", "set": 1, "reps": 12, "weight": 15},
            {"exercise": "Cable Fly", "set": 2, "reps": 12, "weight": 15},
            {"exercise": "Cable Fly", "set": 3, "reps": 12, "weight": 12.5},
            {"exercise": "Push-up", "set": 1, "reps": 15, "weight": 0, "time": "0:45"},
            {"exercise": "Push-up", "set": 2, "reps": 15, "weight": 0, "time": "0:45"},
            {"exercise": "Push-up", "set": 3, "reps": 12, "weight": 0, "time": "0:50", "locked": True},
        ],
    )

    t = _table(db, members[0], trainer1, "Pull Accessories", [3], "18:00", gym.id, None, 1)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Pull-up", "set": 1, "reps": 8, "weight": 0},
            {"exercise": "Pull-up", "set": 2, "reps": 7, "weight": 0},
            {"exercise": "Pull-up", "set": 3, "reps": 6, "weight": 0},
            {"exercise": "Face Pull", "set": 1, "reps": 15, "weight": 25},
            {"exercise": "Face Pull", "set": 2, "reps": 15, "weight": 25},
            {"exercise": "Plank", "set": 1, "reps": 1, "weight": 0, "time": "1:00"},
        ],
    )

    # Taylor — push (Alex)
    t = _table(db, members[1], trainer1, "Push Day", [2, 5], "12:00", gym.id, tpl_push.id, 0)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Overhead Press", "set": 1, "reps": 6, "weight": 50},
            {"exercise": "Overhead Press", "set": 2, "reps": 6, "weight": 50},
            {"exercise": "Overhead Press", "set": 3, "reps": 6, "weight": 47.5},
            {"exercise": "Overhead Press", "set": 4, "reps": 6, "weight": 47.5, "checked": True},
            {"exercise": "Bench Press", "set": 1, "reps": 10, "weight": 60},
            {"exercise": "Bench Press", "set": 2, "reps": 10, "weight": 60},
            {"exercise": "Bench Press", "set": 3, "reps": 10, "weight": 57.5},
            {"exercise": "Lateral Raise", "set": 1, "reps": 12, "weight": 10},
            {"exercise": "Lateral Raise", "set": 2, "reps": 12, "weight": 10},
            {"exercise": "Lateral Raise", "set": 3, "reps": 12, "weight": 8},
            {"exercise": "Tricep Pushdown", "set": 1, "reps": 12, "weight": 30},
            {"exercise": "Tricep Pushdown", "set": 2, "reps": 12, "weight": 30},
            {"exercise": "Dip", "set": 1, "reps": 10, "weight": 0},
            {"exercise": "Dip", "set": 2, "reps": 8, "weight": 0},
        ],
    )

    t = _table(db, members[1], trainer1, "Upper Pump", [6], "10:00", gym.id, None, 1)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Cable Fly", "set": 1, "reps": 15, "weight": 12},
            {"exercise": "Cable Fly", "set": 2, "reps": 15, "weight": 12},
            {"exercise": "Cable Fly", "set": 3, "reps": 15, "weight": 10},
            {"exercise": "Push-up", "set": 1, "reps": 20, "weight": 0},
            {"exercise": "Push-up", "set": 2, "reps": 18, "weight": 0},
        ],
    )

    # Casey — legs (Sam)
    t = _table(db, members[2], trainer2, "Leg Day", [3, 6], "06:00", gym.id, tpl_leg.id, 0)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Barbell Squat", "set": 1, "reps": 5, "weight": 100, "time": "3:00"},
            {"exercise": "Barbell Squat", "set": 2, "reps": 5, "weight": 100, "time": "3:00"},
            {"exercise": "Barbell Squat", "set": 3, "reps": 5, "weight": 97.5, "time": "3:00"},
            {"exercise": "Barbell Squat", "set": 4, "reps": 5, "weight": 97.5, "time": "3:15", "checked": True},
            {"exercise": "Romanian Deadlift", "set": 1, "reps": 8, "weight": 80},
            {"exercise": "Romanian Deadlift", "set": 2, "reps": 8, "weight": 80},
            {"exercise": "Romanian Deadlift", "set": 3, "reps": 8, "weight": 77.5},
            {"exercise": "Leg Press", "set": 1, "reps": 12, "weight": 180},
            {"exercise": "Leg Press", "set": 2, "reps": 12, "weight": 180},
            {"exercise": "Leg Press", "set": 3, "reps": 12, "weight": 170},
            {"exercise": "Walking Lunge", "set": 1, "reps": 12, "weight": 20},
            {"exercise": "Walking Lunge", "set": 2, "reps": 12, "weight": 20},
            {"exercise": "Calf Raise", "set": 1, "reps": 15, "weight": 90},
            {"exercise": "Calf Raise", "set": 2, "reps": 15, "weight": 90},
            {"exercise": "Calf Raise", "set": 3, "reps": 15, "weight": 85},
        ],
    )

    t = _table(db, members[2], trainer2, "Glute & Core", [5], "17:30", gym.id, None, 1)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Hip Thrust", "set": 1, "reps": 10, "weight": 100},
            {"exercise": "Hip Thrust", "set": 2, "reps": 10, "weight": 100},
            {"exercise": "Hip Thrust", "set": 3, "reps": 10, "weight": 95},
            {"exercise": "Bulgarian Split Squat", "set": 1, "reps": 10, "weight": 16},
            {"exercise": "Bulgarian Split Squat", "set": 2, "reps": 10, "weight": 16},
            {"exercise": "Plank", "set": 1, "reps": 1, "weight": 0, "time": "1:30"},
            {"exercise": "Plank", "set": 2, "reps": 1, "weight": 0, "time": "1:15"},
        ],
    )

    # Riley — balanced mix (Sam)
    t = _table(db, members[3], trainer2, "Full Body A", [1, 4], "08:00", gym.id, None, 0)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Barbell Squat", "set": 1, "reps": 8, "weight": 70},
            {"exercise": "Barbell Squat", "set": 2, "reps": 8, "weight": 70},
            {"exercise": "Barbell Squat", "set": 3, "reps": 8, "weight": 67.5},
            {"exercise": "Bench Press", "set": 1, "reps": 8, "weight": 55},
            {"exercise": "Bench Press", "set": 2, "reps": 8, "weight": 55},
            {"exercise": "Bench Press", "set": 3, "reps": 8, "weight": 52.5, "checked": True},
            {"exercise": "Barbell Row", "set": 1, "reps": 10, "weight": 45},
            {"exercise": "Barbell Row", "set": 2, "reps": 10, "weight": 45},
            {"exercise": "Barbell Row", "set": 3, "reps": 10, "weight": 42.5},
            {"exercise": "Plank", "set": 1, "reps": 1, "weight": 0, "time": "0:45"},
        ],
    )

    t = _table(db, members[3], trainer2, "Full Body B", [2, 5], "08:00", gym.id, tpl_push.id, 1)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Romanian Deadlift", "set": 1, "reps": 8, "weight": 65},
            {"exercise": "Romanian Deadlift", "set": 2, "reps": 8, "weight": 65},
            {"exercise": "Romanian Deadlift", "set": 3, "reps": 8, "weight": 62.5},
            {"exercise": "Overhead Press", "set": 1, "reps": 8, "weight": 35},
            {"exercise": "Overhead Press", "set": 2, "reps": 8, "weight": 35},
            {"exercise": "Overhead Press", "set": 3, "reps": 8, "weight": 32.5},
            {"exercise": "Lat Pulldown", "set": 1, "reps": 12, "weight": 50},
            {"exercise": "Lat Pulldown", "set": 2, "reps": 12, "weight": 50},
            {"exercise": "Lat Pulldown", "set": 3, "reps": 12, "weight": 47.5},
            {"exercise": "Pull-up", "set": 1, "reps": 6, "weight": 0},
            {"exercise": "Pull-up", "set": 2, "reps": 5, "weight": 0},
            {"exercise": "Push-up", "set": 1, "reps": 12, "weight": 0},
            {"exercise": "Push-up", "set": 2, "reps": 12, "weight": 0},
        ],
    )

    t = _table(db, members[3], trainer2, "Leg Day Lite", [3], "19:00", gym.id, tpl_leg.id, 2)
    _rows(
        db,
        t,
        exercise_map,
        [
            {"exercise": "Leg Press", "set": 1, "reps": 15, "weight": 140},
            {"exercise": "Leg Press", "set": 2, "reps": 15, "weight": 140},
            {"exercise": "Leg Press", "set": 3, "reps": 15, "weight": 130},
            {"exercise": "Walking Lunge", "set": 1, "reps": 10, "weight": 14},
            {"exercise": "Walking Lunge", "set": 2, "reps": 10, "weight": 14},
            {"exercise": "Calf Raise", "set": 1, "reps": 20, "weight": 70},
            {"exercise": "Calf Raise", "set": 2, "reps": 20, "weight": 70},
        ],
    )

    db.commit()
