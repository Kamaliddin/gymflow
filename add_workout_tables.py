"""Script to add 2 demo workout tables (Push and Pull) to the admin account."""

from database import (
    SessionLocal,
    User,
    UserRole,
    Gym,
    Exercise,
    WorkoutTable,
    TableRow,
    ColumnPermission,
    TABLE_COLUMNS,
)


def add_tables():
    db = SessionLocal()

    # Get or create the default gym
    gym = db.query(Gym).first()
    if not gym:
        gym = Gym(name="GymFlow Default")
        db.add(gym)
        db.flush()

    # Get or create admin user
    admin = db.query(User).filter(User.username == "admin").first()
    if not admin:
        from database import hash_password
        admin = User(
            username="admin",
            password_hash=hash_password("admin"),
            name="Admin",
            surname="User",
            role=UserRole.admin,
            gym_id=gym.id,
        )
        db.add(admin)
        db.flush()

    # Create exercises if they don't exist
    exercise_names = [
        # Push exercises
        "Bench Press",
        "Incline Dumbbell Press",
        "Dip",
        # Pull exercises
        "Barbell Row",
        "Pull-up",
        "Face Pull",
    ]

    exercises = {}
    for name in exercise_names:
        ex = db.query(Exercise).filter(Exercise.name == name).first()
        if not ex:
            ex = Exercise(name=name, is_public=True, gym_id=gym.id)
            db.add(ex)
            db.flush()
        exercises[name] = ex.id

    # PUSH TABLE (Monday, Wednesday, Friday = days 1, 3, 5)
    push_table = db.query(WorkoutTable).filter(
        WorkoutTable.name == "Push",
        WorkoutTable.member_id == admin.id,
    ).first()

    if not push_table:
        push_table = WorkoutTable(
            member_id=admin.id,
            trainer_id=admin.id,
            name="Push",
            default_time="08:00",
            gym_id=gym.id,
        )
        push_table.set_repeat_days([1, 3, 5])  # Mon, Wed, Fri
        db.add(push_table)
        db.flush()

        # Add default column permissions
        for col in TABLE_COLUMNS:
            perm = ColumnPermission(table_id=push_table.id, column_name=col, member_can_edit=True)
            db.add(perm)

        # Add rows for Push exercises (3 exercises x 5 sets each)
        push_exercises = ["Bench Press", "Incline Dumbbell Press", "Dip"]
        row_num = 1

        for exercise_name in push_exercises:
            for set_num in range(1, 6):  # 5 sets
                row = TableRow(
                    table_id=push_table.id,
                    exercise_id=exercises[exercise_name],
                    exercise_name=exercise_name,
                    day_number=1,  # Default to day 1
                    set_number=set_num,
                    rep_goal="8-10" if set_num < 5 else "10-12",  # Last set higher reps
                    weight=185.0 if exercise_name == "Bench Press" else (145.0 if exercise_name == "Incline Dumbbell Press" else 0.0),
                    time_per_set="2:00" if exercise_name != "Dip" else "1:30",
                    checkbox_locked=False,
                    is_checked=False,
                )
                db.add(row)
        db.flush()

    # PULL TABLE (Tuesday, Thursday, Saturday = days 2, 4, 6)
    pull_table = db.query(WorkoutTable).filter(
        WorkoutTable.name == "Pull",
        WorkoutTable.member_id == admin.id,
    ).first()

    if not pull_table:
        pull_table = WorkoutTable(
            member_id=admin.id,
            trainer_id=admin.id,
            name="Pull",
            default_time="09:00",
            gym_id=gym.id,
        )
        pull_table.set_repeat_days([2, 4, 6])  # Tue, Thu, Sat
        db.add(pull_table)
        db.flush()

        # Add default column permissions
        for col in TABLE_COLUMNS:
            perm = ColumnPermission(table_id=pull_table.id, column_name=col, member_can_edit=True)
            db.add(perm)

        # Add rows for Pull exercises (3 exercises x 5 sets each)
        pull_exercises = ["Barbell Row", "Pull-up", "Face Pull"]
        row_num = 1

        for exercise_name in pull_exercises:
            for set_num in range(1, 6):  # 5 sets
                row = TableRow(
                    table_id=pull_table.id,
                    exercise_id=exercises[exercise_name],
                    exercise_name=exercise_name,
                    day_number=2,  # Default to day 2
                    set_number=set_num,
                    rep_goal="6-8" if set_num < 5 else "8-10",  # Last set higher reps
                    weight=225.0 if exercise_name == "Barbell Row" else (0.0 if exercise_name == "Pull-up" else 30.0),
                    time_per_set="2:30" if exercise_name != "Face Pull" else "1:00",
                    checkbox_locked=False,
                    is_checked=False,
                )
                db.add(row)
        db.flush()

    db.commit()
    db.close()

    print("✅ Successfully added Push and Pull workout tables to admin account!")
    print("   - Push table: Monday, Wednesday, Friday (3 exercises × 5 sets)")
    print("   - Pull table: Tuesday, Thursday, Saturday (3 exercises × 5 sets)")


if __name__ == "__main__":
    add_tables()
