"""
HTN Workout Tracker — database.py
All SQLite persistence lives here.
"""

from __future__ import annotations

import hashlib
import os
import sqlite3
from datetime import date, timedelta
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "htn.db")

# -----------------------------------------------------------------------------
# Default Exercise Library & Starter Routines
# -----------------------------------------------------------------------------
DEFAULT_EXERCISES = [
    # 1. Weights + Reps
    ("Bench Press", "Chest", "Barbell", "weights_reps"),
    ("Incline Bench Press", "Chest", "Barbell", "weights_reps"),
    ("Overhead Press", "Shoulders", "Barbell", "weights_reps"),
    ("Barbell Row", "Back", "Barbell", "weights_reps"),
    ("Lat Pulldown", "Back", "Cable", "weights_reps"),
    ("Squat", "Legs", "Barbell", "weights_reps"),
    ("Leg Press", "Legs", "Machine", "weights_reps"),
    ("Romanian Deadlift", "Hamstrings", "Barbell", "weights_reps"),
    ("Deadlift", "Back", "Barbell", "weights_reps"),
    ("Leg Extension", "Quads", "Machine", "weights_reps"),
    ("Leg Curl", "Hamstrings", "Machine", "weights_reps"),
    ("Dumbbell Bicep Curl", "Biceps", "Dumbbell", "weights_reps"),
    ("Dumbbell Lateral Raise", "Shoulders", "Dumbbell", "weights_reps"),
    ("Tricep Pushdown", "Triceps", "Cable", "weights_reps"),
    ("Dumbbell Shoulder Press", "Shoulders", "Dumbbell", "weights_reps"),
    ("Dumbbell Bench Press", "Chest", "Dumbbell", "weights_reps"),

    # 2. Time
    ("Plank", "Core", "Bodyweight", "time"),
    ("Side Plank", "Core", "Bodyweight", "time"),
    ("Wall Sit", "Legs", "Bodyweight", "time"),
    ("Dead Hang", "Back", "Pull-up Bar", "time"),
    ("Treadmill", "Cardio", "Machine", "time"),
    ("Cycling", "Cardio", "Stationary Bike", "time"),
    ("Jump Rope", "Cardio", "Jump Rope", "time"),
    ("Running", "Cardio", "Bodyweight", "time"),
    ("Walking", "Cardio", "Bodyweight", "time"),

    # 3. Bodyweight
    ("Push-ups", "Chest", "Bodyweight", "bodyweight"),
    ("Incline Push-ups", "Chest", "Bodyweight", "bodyweight"),
    ("Diamond Push-ups", "Triceps", "Bodyweight", "bodyweight"),
    ("Pull-ups", "Back", "Pull-up Bar", "bodyweight"),
    ("Chin-ups", "Back", "Pull-up Bar", "bodyweight"),
    ("Bodyweight Squats", "Legs", "Bodyweight", "bodyweight"),
    ("Lunges", "Legs", "Bodyweight", "bodyweight"),
    ("Reverse Lunges", "Legs", "Bodyweight", "bodyweight"),
    ("Bulgarian Split Squats", "Legs", "Bodyweight", "bodyweight"),
    ("Glute Bridge", "Glutes", "Bodyweight", "bodyweight"),
    ("Calf Raises", "Calves", "Bodyweight", "bodyweight"),
    ("Dips", "Chest", "Parallel Bars", "bodyweight"),
    ("Mountain Climbers", "Core", "Bodyweight", "bodyweight"),
    ("Burpees", "Full Body", "Bodyweight", "bodyweight"),

    # 4. Weighted Calisthenics
    ("Weighted Pull-ups", "Back", "Dip Belt", "weighted_calisthenics"),
    ("Weighted Chin-ups", "Back", "Dip Belt", "weighted_calisthenics"),
    ("Weighted Dips", "Chest", "Dip Belt", "weighted_calisthenics"),
    ("Weighted Push-ups", "Chest", "Weight Plate", "weighted_calisthenics"),
    ("Weighted Bulgarian Split Squats", "Legs", "Dumbbell", "weighted_calisthenics"),
    ("Weighted Lunges", "Legs", "Dumbbell", "weighted_calisthenics"),
]

DEFAULT_ROUTINES = [
    (
        "Beginner Full Body: Workout A",
        [
            "Bodyweight Squats",
            "Push-ups",
            "Lat Pulldown",
            "Dumbbell Shoulder Press",
            "Leg Curl",
            "Plank",
        ],
    ),
    (
        "Beginner Full Body: Workout B",
        [
            "Leg Press",
            "Dumbbell Bench Press",
            "Lat Pulldown",
            "Romanian Deadlift",
            "Dumbbell Lateral Raise",
            "Plank",
        ],
    ),
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _columns(conn, table: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _add_column_if_missing(conn, table: str, column: str, definition: str) -> None:
    if column not in _columns(conn, table):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _migrate_unit_pref(conn) -> None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
    ).fetchone()
    if not row:
        return

    create_sql: str = row[0] or ""
    if "'kg'" not in create_sql and "\"kg\"" not in create_sql:
        return

    conn.execute("PRAGMA foreign_keys = OFF")
    conn.execute("ALTER TABLE users RENAME TO _users_old")
    conn.execute(
        """
        CREATE TABLE users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            email         TEXT NOT NULL UNIQUE,
            password      TEXT NOT NULL,
            unit_pref     TEXT DEFAULT 'metric'
                          CHECK(unit_pref IN ('metric', 'imperial')),
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            height_cm     REAL,
            bodyweight_kg REAL,
            body_fat_pct  REAL,
            age           INTEGER,
            sex           TEXT,
            activity_level TEXT,
            calorie_goal  INTEGER,
            calorie_goal_label TEXT,
            display_name  TEXT,
            handle        TEXT,
            seeded_routines INTEGER DEFAULT 0
        )
        """
    )

    old_cols = _columns(conn, "_users_old")
    new_cols_fixed = {
        "id", "username", "email", "password", "created_at",
        "height_cm", "bodyweight_kg", "body_fat_pct", "age", "sex",
        "activity_level", "calorie_goal", "display_name", "handle",
    }
    copy_cols = list(new_cols_fixed & old_cols)
    col_list = ", ".join(copy_cols)

    conn.execute(
        f"""
        INSERT INTO users ({col_list}, unit_pref, calorie_goal_label)
        SELECT {col_list},
               CASE unit_pref
                   WHEN 'kg'  THEN 'metric'
                   WHEN 'lbs' THEN 'imperial'
                   ELSE 'metric'
               END,
               {'calorie_goal_label' if 'calorie_goal_label' in old_cols else "NULL"}
        FROM _users_old
        """
    )
    conn.execute("DROP TABLE _users_old")
    conn.execute("PRAGMA foreign_keys = ON")


def seed_default_exercises(conn) -> None:
    for name, muscle, equip, ex_type in DEFAULT_EXERCISES:
        existing = conn.execute(
            "SELECT id, user_id FROM exercises WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        if not existing:
            conn.execute(
                """
                INSERT INTO exercises (name, muscle_group, equipment, gif_path, user_id, exercise_type, archived)
                VALUES (?, ?, ?, NULL, NULL, ?, 0)
                """,
                (name, muscle, equip, ex_type),
            )
        elif existing["user_id"] is None:
            conn.execute(
                "UPDATE exercises SET exercise_type=?, muscle_group=?, equipment=COALESCE(equipment, ?) WHERE id=?",
                (ex_type, muscle, equip, existing["id"]),
            )


def seed_starter_routines_for_user(user_id: int) -> None:
    conn = get_connection()
    user = conn.execute("SELECT seeded_routines FROM users WHERE id=?", (user_id,)).fetchone()
    if not user or user["seeded_routines"] == 1:
        conn.close()
        return

    # Seed from builtin_routines table if exists, otherwise fallback to DEFAULT_ROUTINES
    b_routines = conn.execute("SELECT id, name FROM builtin_routines ORDER BY id ASC").fetchall()
    if b_routines:
        for br in b_routines:
            cur = conn.execute("INSERT INTO routines (user_id, name) VALUES (?, ?)", (user_id, br["name"]))
            new_rid = cur.lastrowid
            ex_rows = conn.execute(
                "SELECT exercise_id, order_index FROM builtin_routine_exercises WHERE routine_id=? ORDER BY order_index",
                (br["id"],),
            ).fetchall()
            for er in ex_rows:
                conn.execute(
                    "INSERT INTO routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                    (new_rid, er["exercise_id"], er["order_index"]),
                )
    else:
        for routine_name, exercise_names in DEFAULT_ROUTINES:
            cur = conn.execute("INSERT INTO routines (user_id, name) VALUES (?, ?)", (user_id, routine_name))
            routine_id = cur.lastrowid
            for order_idx, ex_name in enumerate(exercise_names):
                ex_row = conn.execute(
                    "SELECT id FROM exercises WHERE lower(name)=lower(?) LIMIT 1", (ex_name,)
                ).fetchone()
                if ex_row:
                    conn.execute(
                        "INSERT INTO routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                        (routine_id, ex_row["id"], order_idx),
                    )

    conn.execute("UPDATE users SET seeded_routines=1 WHERE id=?", (user_id,))
    conn.commit()
    conn.close()


def init_db(force: bool = False):
    try:
        import streamlit as st
        if not force and st.session_state.get("_db_initialized"):
            return
    except Exception:
        pass

    conn = get_connection()

    _migrate_unit_pref(conn)
    conn.commit()

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT NOT NULL UNIQUE,
            email         TEXT NOT NULL UNIQUE,
            password      TEXT NOT NULL,
            unit_pref     TEXT DEFAULT 'metric'
                          CHECK(unit_pref IN ('metric', 'imperial')),
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            muscle_group TEXT NOT NULL,
            equipment TEXT,
            gif_path TEXT
        );

        CREATE TABLE IF NOT EXISTS routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS routine_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            order_index INTEGER NOT NULL,
            FOREIGN KEY (routine_id) REFERENCES routines(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            routine_id INTEGER,
            date DATE DEFAULT CURRENT_DATE,
            duration INTEGER,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (routine_id) REFERENCES routines(id)
        );

        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            set_number INTEGER NOT NULL,
            reps INTEGER,
            weight REAL,
            rpe REAL CHECK(rpe BETWEEN 1 AND 10),
            FOREIGN KEY (session_id) REFERENCES sessions(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );

        CREATE TABLE IF NOT EXISTS builtin_routines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS builtin_routine_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            routine_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            order_index INTEGER NOT NULL,
            FOREIGN KEY (routine_id) REFERENCES builtin_routines(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS builtin_periodization_programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            weeks_count INTEGER DEFAULT 5,
            days_per_week INTEGER DEFAULT 5,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS builtin_periodization_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            week_number INTEGER NOT NULL,
            day_number INTEGER NOT NULL,
            phase_name TEXT NOT NULL,
            phase_badge TEXT,
            objective TEXT,
            day_focus TEXT,
            FOREIGN KEY (program_id) REFERENCES builtin_periodization_programs(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS builtin_periodization_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            day_id INTEGER NOT NULL,
            exercise_id INTEGER,
            exercise_name TEXT NOT NULL,
            muscle_group TEXT NOT NULL,
            exercise_type TEXT NOT NULL DEFAULT 'weights_reps',
            equipment TEXT,
            target TEXT NOT NULL,
            sets INTEGER NOT NULL DEFAULT 2,
            role TEXT NOT NULL DEFAULT 'auxiliary',
            order_index INTEGER NOT NULL,
            FOREIGN KEY (day_id) REFERENCES builtin_periodization_days(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    _add_column_if_missing(conn, "users", "height_cm",           "REAL")
    _add_column_if_missing(conn, "users", "bodyweight_kg",        "REAL")
    _add_column_if_missing(conn, "users", "body_fat_pct",         "REAL")
    _add_column_if_missing(conn, "users", "age",                  "INTEGER")
    _add_column_if_missing(conn, "users", "sex",                  "TEXT")
    _add_column_if_missing(conn, "users", "activity_level",       "TEXT")
    _add_column_if_missing(conn, "users", "calorie_goal",         "INTEGER")
    _add_column_if_missing(conn, "users", "calorie_goal_label",   "TEXT")
    _add_column_if_missing(conn, "users", "display_name",         "TEXT")
    _add_column_if_missing(conn, "users", "handle",               "TEXT")
    _add_column_if_missing(conn, "users", "bio",                  "TEXT")
    _add_column_if_missing(conn, "users", "avatar_b64",           "TEXT")
    _add_column_if_missing(conn, "users", "unit_pref",            "TEXT DEFAULT 'metric'")
    _add_column_if_missing(conn, "users", "theme_pref",           "TEXT DEFAULT 'Original'")
    _add_column_if_missing(conn, "users", "seeded_routines",      "INTEGER DEFAULT 0")

    _add_column_if_missing(conn, "exercises", "user_id",          "INTEGER")
    _add_column_if_missing(conn, "exercises", "exercise_type",    "TEXT NOT NULL DEFAULT 'weights_reps'")
    _add_column_if_missing(conn, "exercises", "archived",         "INTEGER NOT NULL DEFAULT 0")
    _add_column_if_missing(conn, "sets",      "duration_seconds", "INTEGER")
    _add_column_if_missing(conn, "sets",      "set_type",         "TEXT NOT NULL DEFAULT 'working'")
    _add_column_if_missing(conn, "builtin_periodization_programs", "weight_progression_kg", "REAL DEFAULT 2.5")
    _add_column_if_missing(conn, "builtin_periodization_programs", "reps_progression", "INTEGER DEFAULT 1")

    conn.execute(
        "UPDATE users SET display_name=COALESCE(NULLIF(display_name,''),username) "
        "WHERE display_name IS NULL OR display_name=''"
    )
    conn.execute(
        "UPDATE users SET handle=COALESCE(NULLIF(handle,''),username) "
        "WHERE handle IS NULL OR handle=''"
    )

    conn.execute("UPDATE exercises SET exercise_type='weights_reps' WHERE exercise_type='reps'")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS bodyweight_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            weight_kg REAL NOT NULL,
            logged_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )

    try:
        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_nocase "
            "ON users(username COLLATE NOCASE)"
        )
    except sqlite3.IntegrityError:
        pass

    seed_default_exercises(conn)
    seed_builtin_periodization(conn)

    # Seed initial builtin routines into builtin_routines table if empty
    has_b_routines = conn.execute("SELECT 1 FROM builtin_routines LIMIT 1").fetchone()
    if not has_b_routines:
        for r_name, ex_names in DEFAULT_ROUTINES:
            cur = conn.execute("INSERT OR IGNORE INTO builtin_routines (name) VALUES (?)", (r_name,))
            rid = cur.lastrowid
            if rid:
                for idx, ex_n in enumerate(ex_names):
                    ex_r = conn.execute("SELECT id FROM exercises WHERE lower(name)=lower(?) LIMIT 1", (ex_n,)).fetchone()
                    if ex_r:
                        conn.execute(
                            "INSERT INTO builtin_routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                            (rid, ex_r["id"], idx),
                        )

    conn.commit()
    conn.close()

    try:
        import streamlit as st
        st.session_state["_db_initialized"] = True
    except Exception:
        pass


def get_or_create_local_user() -> dict:
    try:
        from auth import restore_login
        restore_login()
    except Exception:
        pass

    try:
        import streamlit as st
        user_id = st.session_state.get("auth_user_id")
        if not user_id:
            st.switch_page("pages/login.py")
            st.stop()
    except ImportError:
        conn = get_connection()
        row = conn.execute("SELECT * FROM users ORDER BY id LIMIT 1").fetchone()
        conn.close()
        if not row:
            raise RuntimeError("No HTN user exists. Start the app through Streamlit and register an account.")
        user_dict = dict(row)
        seed_starter_routines_for_user(user_dict["id"])
        return user_dict

    user = get_user(int(user_id))
    if not user:
        st.session_state.pop("auth_user_id", None)
        st.session_state.pop("auth_username", None)
        st.switch_page("pages/login.py")
        st.stop()

    seed_starter_routines_for_user(user["id"])
    try:
        if "user" not in st.session_state or not isinstance(st.session_state.get("user"), dict):
            st.session_state.user = user
        else:
            st.session_state.user.update(user)

        user_theme = user.get("theme_pref") or get_global_setting("last_active_theme") or "Original"
        st.session_state.theme_pref = user_theme
    except Exception:
        pass
    return user


def get_user(user_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE id=?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_registered_users() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT u.id, u.username, u.email, u.created_at, u.display_name, u.handle,
               (SELECT COUNT(*) FROM sessions s WHERE s.user_id = u.id AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))) AS session_count
        FROM users u
        ORDER BY u.id ASC
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_profile(
    user_id: int,
    *,
    username: str,
    display_name: Optional[str] = None,
    handle: Optional[str] = None,
    bio: Optional[str] = None,
    avatar_b64: Optional[str] = None,
    height_cm: float,
    bodyweight_kg: float,
    body_fat_pct: Optional[float],
    age: Optional[int],
    sex: Optional[str],
    activity_level: Optional[str],
    calorie_goal: Optional[int],
    calorie_goal_label: Optional[str] = None,
    unit_pref: Optional[str] = None,
):
    conn = get_connection()
    conn.execute(
        """
        UPDATE users
        SET username=?, display_name=?, handle=?, height_cm=?, bodyweight_kg=?,
            body_fat_pct=?, age=?, sex=?, activity_level=?, calorie_goal=?,
            calorie_goal_label=?, unit_pref=COALESCE(?, unit_pref)
        WHERE id=?
        """,
        (
            username.strip() or "htn_lifter",
            (display_name or username or "High Tier Normie").strip(),
            (handle or username or "htn_lifter").strip().lstrip("@"),
            height_cm,
            bodyweight_kg,
            body_fat_pct,
            age,
            sex,
            activity_level,
            calorie_goal,
            calorie_goal_label,
            unit_pref if unit_pref in ("metric", "imperial") else None,
            user_id,
        ),
    )

    if bio is not None:
        conn.execute("UPDATE users SET bio=? WHERE id=?", (bio.strip(), user_id))

    if avatar_b64 == "REMOVE":
        conn.execute("UPDATE users SET avatar_b64=NULL WHERE id=?", (user_id,))
    elif avatar_b64 is not None:
        conn.execute("UPDATE users SET avatar_b64=? WHERE id=?", (avatar_b64, user_id))

    if bodyweight_kg and bodyweight_kg > 0:
        conn.execute(
            "INSERT INTO bodyweight_logs (user_id, weight_kg) VALUES (?, ?)",
            (user_id, bodyweight_kg),
        )
    conn.commit()
    conn.close()


def register_user(username: str, email: str, password: str) -> dict:
    conn = get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO users (username,email,password) VALUES (?,?,?)",
            (username.strip(), email.strip().lower(), hashlib.sha256(password.encode()).hexdigest()),
        )
        conn.commit()
        return {"success": True, "user_id": cur.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Username already exists."}
    finally:
        conn.close()


def login_user(username: str, password: str) -> dict:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username.strip(), hashlib.sha256(password.encode()).hexdigest()),
    ).fetchone()
    conn.close()
    return {"success": True, "user": dict(row)} if row else {"success": False, "error": "Invalid username or password."}


def update_unit_pref(user_id: int, unit_pref: str):
    if unit_pref not in ("metric", "imperial"):
        raise ValueError("unit_pref must be 'metric' or 'imperial'")
    conn = get_connection()
    conn.execute("UPDATE users SET unit_pref=? WHERE id=?", (unit_pref, user_id))
    conn.commit()
    conn.close()


def set_global_setting(key: str, value: str) -> bool:
    """Stores or updates a key-value setting in the app_settings table."""
    conn = get_connection()
    try:
        conn.execute(
            """
            INSERT INTO app_settings (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=CURRENT_TIMESTAMP
            """,
            (key, str(value)),
        )
        conn.commit()
        return True
    except Exception:
        return False
    finally:
        conn.close()


def get_global_setting(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieves a setting from the app_settings table."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT value FROM app_settings WHERE key=?", (key,)).fetchone()
        if row and row["value"] is not None:
            return str(row["value"])
        return default
    except Exception:
        return default
    finally:
        conn.close()


def update_theme_pref(user_id: int, theme_name: str) -> bool:
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET theme_pref=? WHERE id=?", (theme_name, user_id))
        conn.commit()
    except Exception:
        return False
    finally:
        conn.close()
    # Always persist the latest active theme to app_settings as well
    set_global_setting("last_active_theme", theme_name)
    return True


def get_theme_pref(user_id: int) -> str:
    conn = get_connection()
    try:
        row = conn.execute("SELECT theme_pref FROM users WHERE id=?", (user_id,)).fetchone()
        if row and row["theme_pref"]:
            return str(row["theme_pref"])
        global_val = get_global_setting("last_active_theme")
        if global_val:
            return global_val
        return "Original"
    except Exception:
        return "Original"
    finally:
        conn.close()



# -------------------- Exercises --------------------

def create_exercise(
    user_id: Optional[int],
    name: str,
    muscle_group: str,
    exercise_type: str = "weights_reps",
    equipment: str = "",
) -> dict:
    name = " ".join((name or "").strip().split())
    muscle_group = muscle_group.strip()
    exercise_type = exercise_type.strip().lower()
    if exercise_type == "reps":
        exercise_type = "weights_reps"

    if not name:
        return {"success": False, "error": "Exercise name is required."}
    if not muscle_group:
        return {"success": False, "error": "Muscle group is required."}
    if exercise_type not in {"weights_reps", "time", "bodyweight", "weighted_calisthenics"}:
        return {
            "success": False,
            "error": "Exercise type must be weights_reps, time, bodyweight, or weighted_calisthenics.",
        }

    conn = get_connection()
    try:
        if user_id is None:
            existing = conn.execute(
                "SELECT id FROM exercises WHERE user_id IS NULL AND lower(name)=lower(?) AND COALESCE(archived,0)=0",
                (name,),
            ).fetchone()
        else:
            existing = conn.execute(
                "SELECT id FROM exercises WHERE (user_id=? OR user_id IS NULL) AND lower(name)=lower(?) AND COALESCE(archived,0)=0",
                (user_id, name),
            ).fetchone()

        if existing:
            return {"success": False, "error": "Exercise already exists."}

        cur = conn.execute(
            """
            INSERT INTO exercises (name,muscle_group,equipment,gif_path,user_id,exercise_type)
            VALUES (?,?,?,?,?,?)
            """,
            (name, muscle_group, equipment.strip() or None, None, user_id, exercise_type),
        )
        conn.commit()
        return {"success": True, "exercise_id": cur.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Exercise already exists."}
    finally:
        conn.close()


def get_builtin_exercises() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM exercises WHERE user_id IS NULL AND COALESCE(archived,0)=0 ORDER BY name"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_builtin_exercise(name: str, muscle_group: str, exercise_type: str, equipment: str = "") -> dict:
    return create_exercise(None, name, muscle_group, exercise_type, equipment)


def delete_builtin_exercise(exercise_id: int) -> dict:
    conn = get_connection()
    try:
        has_history = conn.execute("SELECT 1 FROM sets WHERE exercise_id=? LIMIT 1", (exercise_id,)).fetchone()
        conn.execute("DELETE FROM builtin_routine_exercises WHERE exercise_id=?", (exercise_id,))
        conn.execute("DELETE FROM routine_exercises WHERE exercise_id=?", (exercise_id,))
        if has_history:
            conn.execute("UPDATE exercises SET archived=1 WHERE id=? AND user_id IS NULL", (exercise_id,))
        else:
            conn.execute("DELETE FROM exercises WHERE id=? AND user_id IS NULL", (exercise_id,))
        conn.commit()
        return {"success": True, "error": None}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def get_all_exercises(user_id: Optional[int] = None) -> list:
    conn = get_connection()
    if user_id is None:
        rows = conn.execute("SELECT * FROM exercises WHERE COALESCE(archived, 0)=0 ORDER BY name").fetchall()
    else:
        rows = conn.execute(
            """
            SELECT * FROM exercises
            WHERE (user_id=? OR user_id IS NULL) AND COALESCE(archived, 0)=0
            ORDER BY name
            """,
            (user_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_exercises(query: str, user_id: Optional[int] = None) -> list:
    conn = get_connection()
    like = f"%{query}%"
    if user_id is None:
        rows = conn.execute(
            "SELECT * FROM exercises WHERE (name LIKE ? OR muscle_group LIKE ?) AND COALESCE(archived, 0)=0 ORDER BY name",
            (like, like),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM exercises
               WHERE (user_id=? OR user_id IS NULL)
                 AND (name LIKE ? OR muscle_group LIKE ?)
                 AND COALESCE(archived, 0)=0
               ORDER BY name""",
            (user_id, like, like),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_exercises_by_muscle(muscle_group: str, user_id: Optional[int] = None) -> list:
    conn = get_connection()
    if user_id is None:
        rows = conn.execute(
            "SELECT * FROM exercises WHERE muscle_group=? AND COALESCE(archived, 0)=0 ORDER BY name",
            (muscle_group,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT * FROM exercises
               WHERE (user_id=? OR user_id IS NULL) AND muscle_group=? AND COALESCE(archived, 0)=0
               ORDER BY name""",
            (user_id, muscle_group),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_exercise(
    exercise_id: int,
    user_id: int,
    name: str,
    muscle_group: str,
    exercise_type: str,
    equipment: str = "",
) -> dict:
    name = " ".join((name or "").strip().split())
    muscle_group = muscle_group.strip()
    exercise_type = exercise_type.strip().lower()
    if exercise_type == "reps":
        exercise_type = "weights_reps"

    if not name:
        return {"success": False, "error": "Exercise name is required."}
    if not muscle_group:
        return {"success": False, "error": "Muscle group is required."}
    if exercise_type not in {"weights_reps", "time", "bodyweight", "weighted_calisthenics"}:
        return {"success": False, "error": "Invalid exercise type."}

    conn = get_connection()
    try:
        ex = conn.execute("SELECT id, user_id FROM exercises WHERE id=?", (exercise_id,)).fetchone()
        if not ex:
            return {"success": False, "error": "Exercise not found."}

        duplicate = conn.execute(
            """SELECT id FROM exercises
               WHERE (user_id=? OR user_id IS NULL) AND id<>? AND lower(trim(name))=lower(trim(?)) AND COALESCE(archived,0)=0""",
            (user_id, exercise_id, name),
        ).fetchone()
        if duplicate:
            return {"success": False, "error": "exercise already added"}

        cur = conn.execute(
            """UPDATE exercises
               SET name=?, muscle_group=?, exercise_type=?, equipment=?
               WHERE id=?""",
            (name, muscle_group, exercise_type, equipment.strip() or None, exercise_id),
        )
        conn.commit()
        if cur.rowcount < 1:
            return {"success": False, "error": "Exercise not found."}
        return {"success": True}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "exercise already added"}
    finally:
        conn.close()


def delete_exercise(exercise_id: int, user_id: Optional[int] = None):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, user_id FROM exercises WHERE id=?", (exercise_id,)
        ).fetchone()
        if not row:
            return {"success": False, "error": "Exercise not found."}

        conn.execute("DELETE FROM routine_exercises WHERE exercise_id=?", (exercise_id,))
        conn.execute("DELETE FROM builtin_routine_exercises WHERE exercise_id=?", (exercise_id,))

        has_history = conn.execute(
            "SELECT 1 FROM sets WHERE exercise_id=? LIMIT 1", (exercise_id,)
        ).fetchone()

        if has_history or row["user_id"] is None:
            conn.execute("UPDATE exercises SET archived=1 WHERE id=?", (exercise_id,))
        else:
            conn.execute("DELETE FROM exercises WHERE id=?", (exercise_id,))

        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


# -------------------- Built-in Routines (Admin) --------------------

def get_builtin_routines() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM builtin_routines ORDER BY id ASC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_builtin_routine_exercises(routine_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT e.id, e.name, e.muscle_group, e.exercise_type, bre.order_index
        FROM builtin_routine_exercises bre
        JOIN exercises e ON e.id = bre.exercise_id
        WHERE bre.routine_id = ?
        ORDER BY bre.order_index ASC
        """,
        (routine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_builtin_routine(name: str, exercise_ids: list[int]) -> dict:
    name = (name or "").strip()
    if not name:
        return {"success": False, "error": "Routine name is required."}
    if not exercise_ids:
        return {"success": False, "error": "Choose at least one exercise."}

    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO builtin_routines (name) VALUES (?)", (name,))
        rid = cur.lastrowid
        for idx, eid in enumerate(exercise_ids):
            conn.execute(
                "INSERT INTO builtin_routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                (rid, eid, idx),
            )
        conn.commit()
        return {"success": True, "routine_id": rid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "A built-in routine with this name already exists."}
    finally:
        conn.close()


def delete_builtin_routine(routine_id: int) -> bool:
    conn = get_connection()
    try:
        conn.execute("DELETE FROM builtin_routine_exercises WHERE routine_id=?", (routine_id,))
        conn.execute("DELETE FROM builtin_routines WHERE id=?", (routine_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# -------------------- User Routines --------------------

def create_routine(user_id: int, name: str) -> int:
    conn = get_connection()
    cur = conn.execute("INSERT INTO routines (user_id,name) VALUES (?,?)", (user_id, name.strip()))
    conn.commit()
    conn.close()
    return cur.lastrowid


def update_routine(routine_id: int, user_id: int, name: str, exercise_ids: list[int]) -> dict:
    name = name.strip()
    if not name:
        return {"success": False, "error": "Routine name is required."}
    if not exercise_ids:
        return {"success": False, "error": "Choose at least one exercise."}

    conn = get_connection()
    try:
        row = conn.execute("SELECT id FROM routines WHERE id=? AND user_id=?", (routine_id, user_id)).fetchone()
        if not row:
            return {"success": False, "error": "Routine not found."}

        conn.execute("UPDATE routines SET name=? WHERE id=? AND user_id=?", (name, routine_id, user_id))
        conn.execute("DELETE FROM routine_exercises WHERE routine_id=?", (routine_id,))
        for idx, ex_id in enumerate(exercise_ids):
            conn.execute(
                "INSERT INTO routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                (routine_id, ex_id, idx),
            )
        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


def add_exercise_to_routine(routine_id: int, exercise_id: int, order_index: int):
    conn = get_connection()
    conn.execute(
        "INSERT INTO routine_exercises (routine_id,exercise_id,order_index) VALUES (?,?,?)",
        (routine_id, exercise_id, order_index),
    )
    conn.commit()
    conn.close()


def get_routines(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM routines WHERE user_id=? ORDER BY created_at ASC, id ASC", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_routine_exercises(routine_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT e.id,e.name,e.muscle_group,e.equipment,e.gif_path,e.exercise_type,re.order_index
        FROM routine_exercises re JOIN exercises e ON e.id=re.exercise_id
        WHERE re.routine_id=? ORDER BY re.order_index
        """,
        (routine_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_routine(routine_id: int, user_id: Optional[int] = None):
    conn = get_connection()
    try:
        if user_id is None:
            row = conn.execute("SELECT id FROM routines WHERE id=?", (routine_id,)).fetchone()
        else:
            row = conn.execute("SELECT id FROM routines WHERE id=? AND user_id=?", (routine_id, user_id)).fetchone()
        if not row:
            return False

        conn.execute("UPDATE sessions SET routine_id=NULL WHERE routine_id=?", (routine_id,))
        conn.execute("DELETE FROM routine_exercises WHERE routine_id=?", (routine_id,))
        conn.execute("DELETE FROM routines WHERE id=?", (routine_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# -------------------- Sessions / sets --------------------

def start_session(user_id: int, routine_id: Optional[int] = None) -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO sessions (user_id,routine_id,date) VALUES (?,?,?)",
        (user_id, routine_id, date.today().isoformat()),
    )
    conn.commit()
    conn.close()
    return cur.lastrowid


def finish_session(session_id: int, duration: int, notes: str = ""):
    conn = get_connection()
    conn.execute("UPDATE sessions SET duration=?,notes=? WHERE id=?", (duration, notes.strip(), session_id))
    conn.commit()
    conn.close()


def get_sessions(user_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.*, r.name AS routine_name
        FROM sessions s LEFT JOIN routines r ON r.id=s.routine_id
        WHERE s.user_id=? AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))
        ORDER BY s.date DESC,s.id DESC
        """,
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_session(
    session_id: int,
    user_id: int,
    session_date: str,
    duration: int,
    notes: str = "",
) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, user_id)
        ).fetchone()
        if not row:
            return {"success": False, "error": "Workout not found."}
        conn.execute(
            "UPDATE sessions SET date=?, duration=?, notes=? WHERE id=? AND user_id=?",
            (str(session_date), max(0, int(duration)), (notes or "").strip(), session_id, user_id),
        )
        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


def update_set(
    set_id: int,
    user_id: int,
    reps: Optional[int] = None,
    weight: Optional[float] = None,
    rpe: Optional[float] = None,
    duration_seconds: Optional[int] = None,
    set_type: Optional[str] = None,
    exercise_id: Optional[int] = None,
) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT se.id FROM sets se JOIN sessions s ON s.id=se.session_id
               WHERE se.id=? AND s.user_id=?""",
            (set_id, user_id),
        ).fetchone()
        if not row:
            return {"success": False, "error": "Set not found."}
        if reps is not None:
            reps = max(0, int(reps))
        if weight is not None:
            weight = max(0.0, float(weight))
        if rpe is not None:
            rpe = float(rpe)
            if rpe <= 0:
                rpe = None
            elif rpe > 10:
                return {"success": False, "error": "RPE must be between 1 and 10."}
        if duration_seconds is not None:
            duration_seconds = max(0, int(duration_seconds))
        conn.execute(
            """UPDATE sets SET reps=?, weight=?, rpe=?, duration_seconds=?, set_type=COALESCE(?, set_type),
               exercise_id=COALESCE(?, exercise_id)
               WHERE id=?""",
            (reps, weight, rpe, duration_seconds, set_type, exercise_id, set_id),
        )
        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


def delete_set(set_id: int, user_id: int) -> dict:
    conn = get_connection()
    try:
        row = conn.execute(
            """SELECT se.session_id, se.exercise_id, se.set_number
               FROM sets se JOIN sessions s ON s.id=se.session_id
               WHERE se.id=? AND s.user_id=?""",
            (set_id, user_id),
        ).fetchone()
        if not row:
            return {"success": False, "error": "Set not found."}
        conn.execute("DELETE FROM sets WHERE id=?", (set_id,))
        conn.execute(
            """UPDATE sets SET set_number=set_number-1
               WHERE session_id=? AND exercise_id=? AND set_number>?""",
            (row["session_id"], row["exercise_id"], row["set_number"]),
        )
        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


def delete_session_exercise(session_id: int, exercise_id: int, user_id: int) -> dict:
    conn = get_connection()
    try:
        s = conn.execute("SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, user_id)).fetchone()
        if not s:
            return {"success": False, "error": "Workout not found."}
        conn.execute("DELETE FROM sets WHERE session_id=? AND exercise_id=?", (session_id, exercise_id))
        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


def change_session_exercise(session_id: int, old_exercise_id: int, new_exercise_id: int, user_id: int) -> dict:
    conn = get_connection()
    try:
        s = conn.execute("SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, user_id)).fetchone()
        if not s:
            return {"success": False, "error": "Workout not found."}
        conn.execute(
            "UPDATE sets SET exercise_id=? WHERE session_id=? AND exercise_id=?",
            (new_exercise_id, session_id, old_exercise_id),
        )
        conn.commit()
        return {"success": True, "error": None}
    finally:
        conn.close()


def delete_session(session_id: int, user_id: Optional[int] = None):
    conn = get_connection()
    if user_id is not None:
        ok = conn.execute("SELECT id FROM sessions WHERE id=? AND user_id=?", (session_id, user_id)).fetchone()
        if not ok:
            conn.close()
            return False
    conn.execute("DELETE FROM sets WHERE session_id=?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
    conn.commit()
    conn.close()
    return True


def log_set(
    session_id: int,
    exercise_id: int,
    set_number: int,
    reps: Optional[int] = None,
    weight: Optional[float] = None,
    rpe: Optional[float] = None,
    duration_seconds: Optional[int] = None,
    set_type: str = "working",
):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO sets (session_id,exercise_id,set_number,reps,weight,rpe,duration_seconds,set_type)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (session_id, exercise_id, set_number, reps, weight, rpe, duration_seconds, set_type),
    )
    conn.commit()
    conn.close()


def get_sets_for_session(session_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.*,e.name AS exercise_name,e.exercise_type
        FROM sets s JOIN exercises e ON e.id=s.exercise_id
        WHERE s.session_id=? ORDER BY s.exercise_id,s.set_number
        """,
        (session_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_exercise_personal_bests(user_id: int, exercise_id: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            MAX(se.weight) AS best_weight,
            MAX(se.reps) AS best_reps,
            MAX(se.duration_seconds) AS best_duration
        FROM sets se
        JOIN sessions s ON s.id = se.session_id
        WHERE s.user_id=? AND se.exercise_id=?
        """,
        (user_id, exercise_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else {
        "best_weight": None, "best_reps": None,
        "best_rpe": None, "best_duration": None,
    }


def get_previous_performance(user_id: int, exercise_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT se.set_number,se.reps,se.weight,se.rpe,se.duration_seconds,s.date
        FROM sets se JOIN sessions s ON s.id=se.session_id
        WHERE s.user_id=? AND se.exercise_id=? AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))
          AND s.id=(SELECT s2.id FROM sessions s2 JOIN sets se2 ON se2.session_id=s2.id
                    WHERE s2.user_id=? AND se2.exercise_id=? AND (s2.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s2.id)) ORDER BY s2.date DESC,s2.id DESC LIMIT 1)
        ORDER BY se.set_number ASC
        """,
        (user_id, exercise_id, user_id, exercise_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_progression(user_id: int, exercise_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id AS session_id,
               s.date,
               MAX(se.weight) AS max_weight,
               MAX(se.reps) AS max_reps,
               MAX(se.duration_seconds) AS max_duration,
               MAX(CASE WHEN se.weight IS NOT NULL AND se.reps > 0
                        THEN se.weight * (1 + se.reps / 30.0) ELSE 0 END) AS best_1rm
        FROM sets se
        JOIN sessions s ON s.id = se.session_id
        WHERE s.user_id = ? AND se.exercise_id = ? AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))
        GROUP BY s.id, s.date
        ORDER BY s.date ASC, s.id ASC
        """,
        (user_id, exercise_id),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_estimated_1rm(user_id: int, exercise_id: int) -> float:
    conn = get_connection()
    rows = conn.execute(
        """SELECT se.weight,se.reps FROM sets se JOIN sessions s ON s.id=se.session_id
           WHERE s.user_id=? AND se.exercise_id=? AND se.weight IS NOT NULL AND se.reps>0 AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))""",
        (user_id, exercise_id),
    ).fetchall()
    conn.close()
    if not rows:
        return 0.0
    return round(max(r["weight"] * (1 + r["reps"] / 30) for r in rows), 2)


def get_muscle_group_distribution(user_id: int, start_date: Optional[str] = None) -> list:
    conn = get_connection()
    if start_date:
        rows = conn.execute(
            """
            SELECT e.muscle_group, COUNT(se.id) AS total_sets
            FROM sets se 
            JOIN sessions s ON s.id=se.session_id 
            JOIN exercises e ON e.id=se.exercise_id
            WHERE s.user_id=? AND s.date >= ?
            GROUP BY e.muscle_group 
            ORDER BY total_sets DESC
            """,
            (user_id, start_date),
        ).fetchall()
    else:
        rows = conn.execute(
            """
            SELECT e.muscle_group, COUNT(se.id) AS total_sets
            FROM sets se 
            JOIN sessions s ON s.id=se.session_id 
            JOIN exercises e ON e.id=se.exercise_id
            WHERE s.user_id=? 
            GROUP BY e.muscle_group 
            ORDER BY total_sets DESC
            """,
            (user_id,),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_home_summary(user_id: int) -> dict:
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    conn = get_connection()

    total = conn.execute("SELECT COUNT(*) FROM sessions WHERE user_id=? AND (duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=id))", (user_id,)).fetchone()[0]
    week_sessions = conn.execute(
        "SELECT COUNT(*) FROM sessions WHERE user_id=? AND date>=? AND (duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=id))", (user_id, monday.isoformat())
    ).fetchone()[0]
    last = conn.execute(
        "SELECT MAX(date) FROM sessions WHERE user_id=? AND (duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=id))", (user_id,)
    ).fetchone()[0]
    week_volume = conn.execute(
        """
        SELECT COALESCE(SUM(CASE WHEN se.weight IS NOT NULL AND se.reps IS NOT NULL
                                 THEN se.weight*se.reps ELSE 0 END),0)
        FROM sets se JOIN sessions s ON s.id=se.session_id
        WHERE s.user_id=? AND s.date>=? AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))
        """,
        (user_id, monday.isoformat()),
    ).fetchone()[0]

    dates = [r[0] for r in conn.execute(
        "SELECT DISTINCT date FROM sessions WHERE user_id=? AND (duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=id)) ORDER BY date DESC", (user_id,)
    ).fetchall()]
    conn.close()

    streak = 0
    if dates:
        first = date.fromisoformat(dates[0])
        check = today if first == today else today - timedelta(days=1)
        for d in dates:
            d_date = date.fromisoformat(d)
            if d_date == check:
                streak += 1
                check -= timedelta(days=1)
            else:
                break

    return {"total_sessions": total, "week_sessions": week_sessions, "last_session": last,
            "streak_days": streak, "week_volume": round(week_volume or 0, 1)}


def get_recent_prs(user_id: int, limit: int = 3) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT e.id, e.name, e.exercise_type,
               MAX(se.weight) AS best_weight,
               MAX(se.reps) AS best_reps,
               MAX(se.duration_seconds) AS best_duration,
               MAX(CASE WHEN se.weight IS NOT NULL AND se.reps > 0
                        THEN se.weight * (1 + se.reps / 30.0) ELSE 0 END) AS best_1rm,
               MAX(s.date) AS last_date,
               MAX(s.id) AS last_session_id
        FROM exercises e
        JOIN sets se ON se.exercise_id = e.id
        JOIN sessions s ON s.id = se.session_id
        WHERE s.user_id = ? AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id)) AND (e.user_id = ? OR e.user_id IS NULL)
        GROUP BY e.id, e.name, e.exercise_type
        HAVING COUNT(se.id) > 0
        ORDER BY last_date DESC, last_session_id DESC, best_1rm DESC
        LIMIT ?
        """,
        (user_id, user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_recent_sessions(user_id: int, limit: int = 6) -> list:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT s.id,s.date,s.duration,s.notes,COALESCE(r.name,'Empty Workout') AS name,
               COALESCE((SELECT SUM(CASE WHEN se.weight IS NOT NULL AND se.reps IS NOT NULL
                                          THEN se.weight*se.reps ELSE 0 END)
                         FROM sets se WHERE se.session_id=s.id),0) AS volume,
               (SELECT COUNT(DISTINCT se.exercise_id) FROM sets se WHERE se.session_id=s.id) AS exercises
        FROM sessions s LEFT JOIN routines r ON r.id=s.routine_id
        WHERE s.user_id=? AND (s.duration > 0 OR EXISTS (SELECT 1 FROM sets WHERE session_id=s.id))
        ORDER BY s.date DESC,s.id DESC LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def export_user_data(user_id: int) -> dict:
    user = get_user(user_id) or {}
    conn = get_connection()
    tables = {
        "routines":         [dict(r) for r in conn.execute("SELECT * FROM routines WHERE user_id=?", (user_id,)).fetchall()],
        "sessions":         [dict(r) for r in conn.execute("SELECT * FROM sessions WHERE user_id=?", (user_id,)).fetchall()],
        "sets":             [dict(r) for r in conn.execute(
                                "SELECT se.* FROM sets se JOIN sessions s ON s.id=se.session_id WHERE s.user_id=?", (user_id,)
                            ).fetchall()],
        "exercises":        [dict(r) for r in conn.execute("SELECT * FROM exercises WHERE user_id=? OR user_id IS NULL", (user_id,)).fetchall()],
        "bodyweight_logs":  [dict(r) for r in conn.execute("SELECT * FROM bodyweight_logs WHERE user_id=?", (user_id,)).fetchall()],
    }
    conn.close()
    return {"user": user, **tables}


def delete_account(user_id: int) -> bool:
    conn = get_connection()
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        row = conn.execute("SELECT id FROM users WHERE id=?", (user_id,)).fetchone()
        if not row:
            return False

        conn.execute("DELETE FROM auth_sessions WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM bodyweight_logs WHERE user_id=?", (user_id,))

        conn.execute(
            "DELETE FROM sets WHERE session_id IN (SELECT id FROM sessions WHERE user_id=?)",
            (user_id,),
        )
        conn.execute(
            "DELETE FROM sets WHERE exercise_id IN (SELECT id FROM exercises WHERE user_id=?)",
            (user_id,),
        )

        conn.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))

        conn.execute(
            "DELETE FROM routine_exercises WHERE routine_id IN (SELECT id FROM routines WHERE user_id=?)",
            (user_id,),
        )
        conn.execute(
            "DELETE FROM routine_exercises WHERE exercise_id IN (SELECT id FROM exercises WHERE user_id=?)",
            (user_id,),
        )

        conn.execute("DELETE FROM routines WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM exercises WHERE user_id=?", (user_id,))
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))

        conn.commit()
        return True
    finally:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.close()

# -------------------- Built-in Periodization Mesocycle (Admin & Lifters) --------------------

DEFAULT_PERIODIZATION_DATA = {
    "name": "HTN 5-Week Periodization Mesocycle",
    "description": "Periodized progression for Pull-ups, Bench Press, and Zercher Squats with hypertrophy support accessories.",
    "weeks": {
        1: {
            "phase": "Hypertrophy",
            "badge": "2x8-10 \u00b7 RPE 9-10",
            "objective": "High-volume hypertrophy foundation and structural adaptation",
            "days": {
                1: [{"name": "Weighted Pull-ups", "target": "2x8-10 (RPE 9-10)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Bicep Curls", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Cable Rear Delt Fly", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Bench Press (Bottom Half)", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Extension", "target": "2x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "T Bar Row", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}],
                2: [{"name": "Bench Press", "target": "2x8-10 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Zercher Squats (Bottom Half)", "target": "2x8-10", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Curl", "target": "2x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Incline Barbell Bench", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "support"}, {"name": "Lateral Raise", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"}],
                3: [{"name": "Zercher Squats", "target": "2x8-10 (RPE 9-10)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Leg Extension", "target": "2x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Leg Curl", "target": "2x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Weighted Pull-ups (Top Half)", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "2x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "auxiliary"}],
                4: [{"name": "Weighted Pull-ups", "target": "2x8-10 (RPE 9-10)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Cable Rear Delt Fly", "target": "2x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Bicep Curls", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "T Bar Row", "target": "2x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}],
                5: [{"name": "Bench Press", "target": "2x8-10 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Zercher Squats (Bottom Half)", "target": "2x8-10", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Bicep Curls", "target": "2x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Incline Barbell Bench", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "support"}, {"name": "Lateral Raise", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"}],
            },
        },
        2: {
            "phase": "Singles",
            "badge": "4x1 (RPE 8-9) \u00b7 Paused 2x5 (RPE 8)",
            "objective": "Maximal neural recruitment with paused technical mastery",
            "days": {
                1: [{"name": "Weighted Pull-ups", "target": "4x1 (RPE 8-9)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 4, "role": "focus"}, {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Bicep Curls", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Cable Rear Delt Fly", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Paused Bench Press", "target": "2x5 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"}, {"name": "T Bar Row", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                2: [{"name": "Bench Press", "target": "4x1 (RPE 8-9)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 4, "role": "focus"}, {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"}, {"name": "Incline Barbell Bench", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 1, "role": "support"}, {"name": "Lateral Raise", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"}],
                3: [{"name": "Zercher Squats", "target": "4x1 (RPE 8-9)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 4, "role": "focus"}, {"name": "Leg Extension", "target": "1x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Leg Curl", "target": "1x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Paused Weighted Pull-ups (Top Half)", "target": "2x5 (RPE 8)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"}],
                4: [{"name": "Weighted Pull-ups", "target": "4x1 (RPE 8-9)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 4, "role": "focus"}, {"name": "Machine Chest Press", "target": "2x8-10 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Cable Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Bicep Curls", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "T Bar Row", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                5: [{"name": "Bench Press", "target": "4x1 (RPE 8-9)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 4, "role": "focus"}, {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Bicep Curls", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Incline Barbell Bench", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 1, "role": "support"}, {"name": "Lateral Raise", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"}],
            },
        },
        3: {
            "phase": "Conditioning",
            "badge": "2x5 [Slow Eccentrics] \u00b7 RPE 8",
            "objective": "Eccentric control and mechanical tension under strict tempo",
            "days": {
                1: [{"name": "Weighted Pull-ups", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Paused Bench Press", "target": "2x5 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Extension", "target": "2x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Bicep Curls", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Cable Rear Delt Fly", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "T Bar Row", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}],
                2: [{"name": "Bench Press", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Curl", "target": "2x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Incline Barbell Bench", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "support"}, {"name": "Lateral Raise", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"}],
                3: [{"name": "Zercher Squats", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Paused Weighted Pull-ups (Top Half)", "target": "2x5 (RPE 8)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "2x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "auxiliary"}, {"name": "Leg Extension", "target": "2x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Leg Curl", "target": "2x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}],
                4: [{"name": "Weighted Pull-ups", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Machine Chest Press", "target": "2x8-10 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Cable Rear Delt Fly", "target": "2x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Lat Pullover", "target": "2x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Bicep Curls", "target": "2x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "T Bar Row", "target": "2x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}],
                5: [{"name": "Bench Press", "target": "2x5 [Slow Eccentrics] (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Paused Zercher Squats", "target": "2x5 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Bicep Curls", "target": "2x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "support"}, {"name": "Overhead Extension", "target": "2x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 2, "role": "support"}, {"name": "Incline Barbell Bench", "target": "2x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "support"}, {"name": "Lateral Raise", "target": "2x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 2, "role": "support"}],
            },
        },
        4: {
            "phase": "Strength",
            "badge": "2x3 (RPE 9-10) \u00b7 Paused 2x3 (RPE 8)",
            "objective": "Heavy intensity work pushing near-maximal neuromuscular limits",
            "days": {
                1: [{"name": "Weighted Pull-ups", "target": "2x3 (RPE 9-10)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Paused Bench Press", "target": "2x3 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Bicep Curls", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Cable Rear Delt Fly", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "T Bar Row", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                2: [{"name": "Bench Press", "target": "2x3 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Paused Zercher Squats", "target": "2x3 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Incline Barbell Bench", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 1, "role": "support"}, {"name": "Lateral Raise", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"}],
                3: [{"name": "Zercher Squats", "target": "2x3 (RPE 9-10)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Paused Weighted Pull-ups (Top Half)", "target": "2x3 (RPE 8)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"}, {"name": "Leg Extension", "target": "1x8-10", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Leg Curl", "target": "1x8-10", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                4: [{"name": "Weighted Pull-ups", "target": "2x3 (RPE 9-10)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Machine Chest Press", "target": "1-2x8-10 (RPE 8)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Cable Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Lat Pullover", "target": "1x8-10", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Bicep Curls", "target": "1x8-10", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "T Bar Row", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                5: [{"name": "Bench Press", "target": "2x3 (RPE 9-10)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Paused Zercher Squats", "target": "2x3 (RPE 8)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Bicep Curls", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Overhead Extension", "target": "1x8-10", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Incline Barbell Bench", "target": "1x8-10", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 1, "role": "support"}, {"name": "Lateral Raise", "target": "1x8-10", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"}],
            },
        },
        5: {
            "phase": "Deload",
            "badge": "2x6 (RPE 7) \u00b7 Active Recovery",
            "objective": "Active CNS dissipation, joint recovery and technique priming",
            "days": {
                1: [{"name": "Weighted Pull-ups", "target": "2x6 (RPE 7)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Bench Press", "target": "2x6 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Bicep Curls", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Cable Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "T Bar Row", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                2: [{"name": "Bench Press", "target": "2x6 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Zercher Squats", "target": "2x6 (RPE 7)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "1x10-15", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Overhead Extension", "target": "1x10-15", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Incline Barbell Bench", "target": "1x10-15", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 1, "role": "support"}, {"name": "Lateral Raise", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"}],
                3: [{"name": "Zercher Squats", "target": "2x6 (RPE 7)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Weighted Pull-ups", "target": "2x6 (RPE 7)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "auxiliary"}, {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"}, {"name": "Leg Extension", "target": "1x10-15", "muscle": "Quads", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Leg Curl", "target": "1x10-15", "muscle": "Hamstrings", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                4: [{"name": "Weighted Pull-ups", "target": "2x6 (RPE 7)", "muscle": "Back", "type": "weights_reps", "equip": "Pull-up Bar", "sets": 2, "role": "focus"}, {"name": "Machine Chest Press", "target": "2x10 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 2, "role": "auxiliary"}, {"name": "Cable Rear Delt Fly", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Lat Pullover", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Bicep Curls", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "T Bar Row", "target": "1x10-15", "muscle": "Back", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}],
                5: [{"name": "Bench Press", "target": "2x6 (RPE 7)", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "focus"}, {"name": "Zercher Squats", "target": "2x6 (RPE 7)", "muscle": "Legs", "type": "weights_reps", "equip": "Barbell", "sets": 2, "role": "auxiliary"}, {"name": "Bicep Curls", "target": "1x10-15", "muscle": "Biceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "auxiliary"}, {"name": "Machine Chest Press", "target": "1x10-15", "muscle": "Chest", "type": "weights_reps", "equip": "Machine", "sets": 1, "role": "support"}, {"name": "Overhead Extension", "target": "1x10-15", "muscle": "Triceps", "type": "weights_reps", "equip": "Cable", "sets": 1, "role": "support"}, {"name": "Incline Barbell Bench", "target": "1x10-15", "muscle": "Chest", "type": "weights_reps", "equip": "Barbell", "sets": 1, "role": "support"}, {"name": "Lateral Raise", "target": "1x10-15", "muscle": "Shoulders", "type": "weights_reps", "equip": "Dumbbell", "sets": 1, "role": "support"}],
            },
        },
    },
}


def seed_builtin_periodization(conn) -> None:
    """Seeds the built-in periodization cycle into SQLite if not present."""
    row = conn.execute("SELECT id FROM builtin_periodization_programs LIMIT 1").fetchone()
    if row:
        return

    cur = conn.execute(
        "INSERT INTO builtin_periodization_programs (name, description, weeks_count, days_per_week) VALUES (?, ?, 5, 5)",
        (DEFAULT_PERIODIZATION_DATA["name"], DEFAULT_PERIODIZATION_DATA["description"]),
    )
    prog_id = cur.lastrowid

    for w_num, w_info in DEFAULT_PERIODIZATION_DATA["weeks"].items():
        phase = w_info["phase"]
        badge = w_info["badge"]
        objective = w_info["objective"]
        for d_num, d_exs in w_info["days"].items():
            cur_d = conn.execute(
                """
                INSERT INTO builtin_periodization_days
                (program_id, week_number, day_number, phase_name, phase_badge, objective, day_focus)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (prog_id, w_num, d_num, phase, badge, objective, f"Day {d_num}"),
            )
            day_id = cur_d.lastrowid

            for idx, ex_data in enumerate(d_exs):
                ex_name = ex_data["name"]
                ex_muscle = ex_data["muscle"]
                ex_type = ex_data.get("type", "weights_reps")
                ex_equip = ex_data.get("equip", "")
                ex_target = ex_data["target"]
                ex_sets = int(ex_data.get("sets", 2))
                ex_role = ex_data.get("role", "auxiliary")

                # Match exercise id if existing in exercises table
                e_row = conn.execute(
                    "SELECT id FROM exercises WHERE lower(name)=lower(?) LIMIT 1", (ex_name,)
                ).fetchone()
                e_id = e_row["id"] if e_row else None

                conn.execute(
                    """
                    INSERT INTO builtin_periodization_exercises
                    (day_id, exercise_id, exercise_name, muscle_group, exercise_type, equipment, target, sets, role, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (day_id, e_id, ex_name, ex_muscle, ex_type, ex_equip, ex_target, ex_sets, ex_role, idx),
                )
    conn.commit()


def get_builtin_periodization_program(program_id: Optional[int] = None) -> dict:
    """Retrieves the full in-built periodization structure from SQLite."""
    conn = get_connection()
    try:
        if program_id:
            prog_row = conn.execute("SELECT * FROM builtin_periodization_programs WHERE id=?", (program_id,)).fetchone()
        else:
            prog_row = conn.execute("SELECT * FROM builtin_periodization_programs ORDER BY id ASC LIMIT 1").fetchone()

        if not prog_row:
            seed_builtin_periodization(conn)
            prog_row = conn.execute("SELECT * FROM builtin_periodization_programs ORDER BY id ASC LIMIT 1").fetchone()
            if not prog_row:
                return DEFAULT_PERIODIZATION_DATA["weeks"]

        p_id = prog_row["id"]
        days_rows = conn.execute(
            """
            SELECT * FROM builtin_periodization_days
            WHERE program_id=?
            ORDER BY week_number ASC, day_number ASC
            """,
            (p_id,),
        ).fetchall()

        weeks_map = {}
        for d in days_rows:
            w_num = d["week_number"]
            d_num = d["day_number"]
            d_id = d["id"]

            if w_num not in weeks_map:
                weeks_map[w_num] = {
                    "phase": d["phase_name"],
                    "badge": d["phase_badge"],
                    "objective": d["objective"] or "",
                    "days": {},
                    "day_meta": {},
                }

            weeks_map[w_num]["day_meta"][d_num] = {
                "id": d_id,
                "phase_name": d["phase_name"],
                "phase_badge": d["phase_badge"],
                "objective": d["objective"] or "",
                "day_focus": d["day_focus"] or "",
            }

            ex_rows = conn.execute(
                """
                SELECT * FROM builtin_periodization_exercises
                WHERE day_id=?
                ORDER BY order_index ASC
                """,
                (d_id,),
            ).fetchall()

            exercise_list = []
            for er in ex_rows:
                exercise_list.append({
                    "id": er["id"],
                    "day_id": d_id,
                    "name": er["exercise_name"],
                    "muscle": er["muscle_group"],
                    "type": er["exercise_type"],
                    "equip": er["equipment"] or "",
                    "target": er["target"],
                    "sets": er["sets"],
                    "role": er["role"],
                    "order_index": er["order_index"],
                })

            weeks_map[w_num]["days"][d_num] = exercise_list

        return weeks_map
    finally:
        conn.close()


def get_all_periodization_programs() -> list:
    """Retrieves all periodization programs (built-in and custom)."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM builtin_periodization_programs ORDER BY id ASC").fetchall()
        if not rows:
            seed_builtin_periodization(conn)
            rows = conn.execute("SELECT * FROM builtin_periodization_programs ORDER BY id ASC").fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_periodization_program_metadata(program_id: int) -> Optional[dict]:
    """Retrieves metadata for a specific periodization program."""
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM builtin_periodization_programs WHERE id=?", (program_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_periodization_program(
    name: str,
    description: str = "",
    weeks_count: int = 5,
    days_per_week: int = 5,
    template_program_id: Optional[int] = None,
    weight_progression_kg: Optional[float] = None,
    reps_progression: Optional[int] = None,
) -> dict:
    """Creates a new periodization program (either cloned from a template or initialized blank)."""
    clean_name = " ".join((name or "").strip().split())
    if not clean_name:
        return {"success": False, "error": "Program name is required."}
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM builtin_periodization_programs WHERE lower(name) = lower(?)", (clean_name,)
        ).fetchone()
        if existing:
            clean_name = f"{clean_name} ({date.today().isoformat()})"

        if template_program_id and (weight_progression_kg is None or reps_progression is None):
            tmpl_row = conn.execute("SELECT * FROM builtin_periodization_programs WHERE id=?", (template_program_id,)).fetchone()
            if tmpl_row:
                if weight_progression_kg is None and ("weight_progression_kg" in tmpl_row.keys()) and tmpl_row["weight_progression_kg"] is not None:
                    weight_progression_kg = float(tmpl_row["weight_progression_kg"])
                if reps_progression is None and ("reps_progression" in tmpl_row.keys()) and tmpl_row["reps_progression"] is not None:
                    reps_progression = int(tmpl_row["reps_progression"])

        final_w_prog = max(0.25, float(weight_progression_kg if weight_progression_kg is not None else 2.5))
        final_r_prog = max(1, int(reps_progression if reps_progression is not None else 1))

        cur = conn.execute(
            """
            INSERT INTO builtin_periodization_programs
            (name, description, weeks_count, days_per_week, weight_progression_kg, reps_progression)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                clean_name,
                (description or "").strip(),
                max(1, int(weeks_count)),
                max(1, int(days_per_week)),
                final_w_prog,
                final_r_prog,
            ),
        )
        new_prog_id = cur.lastrowid

        if template_program_id:
            t_days = conn.execute(
                "SELECT * FROM builtin_periodization_days WHERE program_id=? ORDER BY week_number, day_number",
                (template_program_id,),
            ).fetchall()
            for td in t_days:
                cur_d = conn.execute(
                    """
                    INSERT INTO builtin_periodization_days
                    (program_id, week_number, day_number, phase_name, phase_badge, objective, day_focus)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (new_prog_id, td["week_number"], td["day_number"], td["phase_name"], td["phase_badge"], td["objective"], td["day_focus"]),
                )
                new_day_id = cur_d.lastrowid

                t_exs = conn.execute(
                    "SELECT * FROM builtin_periodization_exercises WHERE day_id=? ORDER BY order_index",
                    (td["id"],),
                ).fetchall()
                for te in t_exs:
                    conn.execute(
                        """
                        INSERT INTO builtin_periodization_exercises
                        (day_id, exercise_id, exercise_name, muscle_group, exercise_type, equipment, target, sets, role, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (new_day_id, te["exercise_id"], te["exercise_name"], te["muscle_group"], te["exercise_type"], te["equipment"], te["target"], te["sets"], te["role"], te["order_index"]),
                    )
        else:
            for w in range(1, int(weeks_count) + 1):
                for d in range(1, int(days_per_week) + 1):
                    conn.execute(
                        """
                        INSERT INTO builtin_periodization_days
                        (program_id, week_number, day_number, phase_name, phase_badge, objective, day_focus)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (new_prog_id, w, d, f"Week {w}", "Custom Target", f"Training objectives for Week {w} Day {d}", f"Day {d}"),
                    )

        conn.commit()
        return {"success": True, "program_id": new_prog_id, "name": clean_name}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def duplicate_periodization_program(source_program_id: int, new_name: Optional[str] = None) -> dict:
    """Clones an existing periodization cycle into a new custom cycle."""
    conn = get_connection()
    try:
        source = conn.execute("SELECT * FROM builtin_periodization_programs WHERE id=?", (source_program_id,)).fetchone()
        if not source:
            return {"success": False, "error": "Source periodization program not found."}
        if not new_name:
            new_name = f"{source['name']} (Copy)"

        w_prog = source["weight_progression_kg"] if "weight_progression_kg" in source.keys() and source["weight_progression_kg"] is not None else 2.5
        r_prog = source["reps_progression"] if "reps_progression" in source.keys() and source["reps_progression"] is not None else 1

        return create_periodization_program(
            name=new_name,
            description=source["description"] or "",
            weeks_count=source["weeks_count"] or 5,
            days_per_week=source["days_per_week"] or 5,
            template_program_id=source_program_id,
            weight_progression_kg=float(w_prog),
            reps_progression=int(r_prog),
        )
    finally:
        conn.close()


def update_periodization_program_settings(
    program_id: int,
    weight_progression_kg: float,
    reps_progression: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> dict:
    """Updates progressive overload settings and metadata for a cycle."""
    conn = get_connection()
    try:
        w_val = max(0.25, float(weight_progression_kg))
        r_val = max(1, int(reps_progression))
        if name is not None and name.strip():
            conn.execute(
                """
                UPDATE builtin_periodization_programs
                SET weight_progression_kg=?, reps_progression=?, name=?, description=?
                WHERE id=?
                """,
                (w_val, r_val, name.strip(), (description or "").strip(), program_id),
            )
        else:
            conn.execute(
                """
                UPDATE builtin_periodization_programs
                SET weight_progression_kg=?, reps_progression=?
                WHERE id=?
                """,
                (w_val, r_val, program_id),
            )
        conn.commit()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def advance_periodization_cycle_with_overload(
    source_program_id: int,
    custom_wave_name: Optional[str] = None,
) -> dict:
    """
    Creates the next mesocycle wave based on an existing cycle, applying
    the configured progressive overload increment to the exercise targets.
    """
    conn = get_connection()
    try:
        source = conn.execute("SELECT * FROM builtin_periodization_programs WHERE id=?", (source_program_id,)).fetchone()
        if not source:
            return {"success": False, "error": "Source cycle not found."}

        base_name = source["name"]
        prog_kg = float(source["weight_progression_kg"] if "weight_progression_kg" in source.keys() and source["weight_progression_kg"] is not None else 2.5)
        prog_reps = int(source["reps_progression"] if "reps_progression" in source.keys() and source["reps_progression"] is not None else 1)

        import re
        wave_match = re.search(r'Wave\s*([0-9]+)', base_name, re.IGNORECASE)
        if wave_match:
            curr_wave = int(wave_match.group(1))
            new_wave = curr_wave + 1
            wave_name = custom_wave_name or re.sub(r'Wave\s*[0-9]+', f'Wave {new_wave}', base_name, flags=re.IGNORECASE)
        else:
            wave_name = custom_wave_name or f"{base_name} (Wave 2)"

        res = create_periodization_program(
            name=wave_name,
            description=f"Progressive overload wave from {base_name}. Overload rate: +{prog_kg}kg / +{prog_reps} reps per cycle.",
            weeks_count=source["weeks_count"] or 5,
            days_per_week=source["days_per_week"] or 5,
            template_program_id=source_program_id,
            weight_progression_kg=prog_kg,
            reps_progression=prog_reps,
        )
        if not res.get("success"):
            return res

        return {
            "success": True,
            "program_id": res["program_id"],
            "name": wave_name,
            "overload_kg": prog_kg,
            "overload_reps": prog_reps,
        }
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def calculate_progressive_overload_suggestion(
    user_id: int,
    exercise_id: int,
    prescribed_target: str = "",
    exercise_type: str = "weights_reps",
    cycle_prog_kg: float = 2.5,
    cycle_prog_reps: int = 1,
) -> dict:
    """
    Computes an intelligent weight & reps suggestion for an exercise based on:
    1. Prescribed periodization target (e.g. 2x8-10, 4x1, 2x5)
    2. Previous performance in past workouts
    3. All-time personal bests
    4. Configured cycle progressive overload increment
    """
    conn = get_connection()
    try:
        prev_rows = conn.execute(
            """
            SELECT s.weight, s.reps, s.rpe, s.duration_seconds
            FROM sets s
            JOIN sessions sess ON s.session_id = sess.id
            WHERE sess.user_id = ? AND s.exercise_id = ? AND sess.duration > 0
            ORDER BY sess.date DESC, s.id DESC
            LIMIT 5
            """,
            (user_id, exercise_id),
        ).fetchall()

        bests_row = conn.execute(
            """
            SELECT MAX(s.weight) AS best_w, MAX(s.reps) AS best_r
            FROM sets s
            JOIN sessions sess ON s.session_id = sess.id
            WHERE sess.user_id = ? AND s.exercise_id = ?
            """,
            (user_id, exercise_id),
        ).fetchone()

        best_w = bests_row["best_w"] if bests_row and bests_row["best_w"] is not None else 0.0
        best_r = bests_row["best_r"] if bests_row and bests_row["best_r"] is not None else 0

        target_clean = (prescribed_target or "").lower()
        target_reps = 8
        target_rpe = 8.5
        import re

        rep_match = re.search(r'(?:[0-9]+x)?([0-9]+)(?:-([0-9]+))?', target_clean)
        if rep_match:
            low_r = int(rep_match.group(1))
            high_r = int(rep_match.group(2)) if rep_match.group(2) else low_r
            target_reps = high_r if high_r > 0 else 8
            rep_label = f"{low_r}-{high_r}" if high_r > low_r else str(low_r)
        else:
            rep_label = "8-10"

        rpe_match = re.search(r'rpe\s*([0-9]+(?:\.[0-9]+)?)(?:-([0-9]+(?:\.[0-9]+)?))?', target_clean)
        if rpe_match:
            target_rpe = float(rpe_match.group(2) if rpe_match.group(2) else rpe_match.group(1))

        if not prev_rows:
            if exercise_type == "bodyweight":
                return {
                    "weight": 0.0,
                    "reps": target_reps,
                    "rpe": target_rpe,
                    "reason": f"Baseline target: {rep_label} reps @ RPE {target_rpe}",
                    "overload_applied": False,
                }
            elif best_w > 0:
                sug_w = round(best_w * 0.9, 1)
                return {
                    "weight": sug_w,
                    "reps": target_reps,
                    "rpe": target_rpe,
                    "reason": f"Baseline: ~90% of PR ({sug_w} kg × {rep_label} reps)",
                    "overload_applied": False,
                }
            else:
                return {
                    "weight": 20.0,
                    "reps": target_reps,
                    "rpe": target_rpe,
                    "reason": f"Baseline: {rep_label} reps @ RPE {target_rpe}",
                    "overload_applied": False,
                }

        last_s = prev_rows[0]
        last_w = float(last_s["weight"] or 0.0)
        last_r = int(last_s["reps"] or 0)
        last_rpe = float(last_s["rpe"] or 8.0)
        last_dur = int(last_s["duration_seconds"] or 0)

        if exercise_type == "time":
            sug_dur = last_dur + 5 if last_dur > 0 else 45
            return {
                "duration": sug_dur,
                "weight": 0.0,
                "reps": 0,
                "rpe": target_rpe,
                "reason": f"+5s endurance overload over last session ({last_dur}s)",
                "overload_applied": True,
            }

        if exercise_type == "bodyweight":
            sug_r = max(target_reps, last_r + cycle_prog_reps)
            return {
                "weight": 0.0,
                "reps": sug_r,
                "rpe": target_rpe,
                "reason": f"+{cycle_prog_reps} rep progression (Last: {last_r} reps)",
                "overload_applied": True,
            }

        if (last_rpe <= 9.0 or last_rpe == 0) and (last_r >= target_reps):
            sug_w = round(last_w + cycle_prog_kg, 2)
            sug_r = target_reps
            reason = f"+{cycle_prog_kg}kg overload (Last: {last_w}kg × {last_r} @ RPE {last_rpe})"
            overload = True
        elif last_r < target_reps:
            sug_w = last_w
            sug_r = last_r + cycle_prog_reps
            reason = f"+{cycle_prog_reps} rep progression at {last_w}kg (Target: {target_reps} reps)"
            overload = True
        else:
            sug_w = round(last_w + cycle_prog_kg, 2)
            sug_r = target_reps
            reason = f"+{cycle_prog_kg}kg overload progression"
            overload = True

        return {
            "weight": max(0.0, sug_w),
            "reps": max(1, sug_r),
            "rpe": target_rpe,
            "reason": reason,
            "overload_applied": overload,
        }
    finally:
        conn.close()


def delete_periodization_program(program_id: int) -> dict:
    """Deletes a periodization cycle and its child days and exercises. Prevents deleting if it is the only remaining cycle."""
    conn = get_connection()
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM builtin_periodization_programs").fetchone()["c"]
        if count <= 1:
            return {"success": False, "error": "Cannot delete the only remaining periodization cycle."}

        prog_row = conn.execute("SELECT id, name FROM builtin_periodization_programs WHERE id=?", (program_id,)).fetchone()
        if not prog_row:
            return {"success": False, "error": "Periodization cycle not found."}

        prog_name = prog_row["name"]

        # Explicitly delete child exercises and days to ensure clean cascading regardless of SQLite FK pragma state
        conn.execute(
            """
            DELETE FROM builtin_periodization_exercises
            WHERE day_id IN (SELECT id FROM builtin_periodization_days WHERE program_id=?)
            """,
            (program_id,),
        )
        conn.execute("DELETE FROM builtin_periodization_days WHERE program_id=?", (program_id,))
        conn.execute("DELETE FROM builtin_periodization_programs WHERE id=?", (program_id,))
        conn.commit()
        return {"success": True, "name": prog_name}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def normalize_periodization_role(role_val: str) -> str:
    """Normalizes role strings to 'focus', 'support', or 'auxiliary'."""
    r = (role_val or "").strip().lower()
    if "focus" in r or "primary" in r:
        return "focus"
    elif "support" in r or "hypertrophy" in r:
        return "support"
    else:
        return "auxiliary"


def normalize_periodization_exercise_type(ex_type: str) -> str:
    """Normalizes tracking types to standard DB representation."""
    t = (ex_type or "weights_reps").strip().lower()
    if t in ("weights + reps", "weights_reps", "reps", "weights and reps"):
        return "weights_reps"
    elif t in ("time", "duration"):
        return "time"
    elif t in ("bodyweight", "body weight", "bw"):
        return "bodyweight"
    elif t in ("weighted calisthenics", "weighted_calisthenics"):
        return "weighted_calisthenics"
    return "weights_reps"


def get_or_create_periodization_day(program_id: int, week_number: int, day_number: int) -> int:
    """Retrieves the day_id for the given program, week, and day, creating it if it doesn't exist."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id FROM builtin_periodization_days WHERE program_id=? AND week_number=? AND day_number=?",
            (program_id, week_number, day_number),
        ).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            """
            INSERT INTO builtin_periodization_days (program_id, week_number, day_number, phase_name, phase_badge, objective, day_focus)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (program_id, week_number, day_number, f"Week {week_number}", "Custom Target", f"Training objectives for Week {week_number} Day {day_number}", f"Day {day_number}"),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_periodization_day_info(program_id: int, week_number: int, day_number: int) -> dict:
    """Retrieves full day metadata dictionary (id, phase_name, phase_badge, objective, etc.)."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM builtin_periodization_days WHERE program_id=? AND week_number=? AND day_number=?",
            (program_id, week_number, day_number),
        ).fetchone()
        if row:
            return dict(row)
        cur = conn.execute(
            """
            INSERT INTO builtin_periodization_days (program_id, week_number, day_number, phase_name, phase_badge, objective, day_focus)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (program_id, week_number, day_number, f"Week {week_number}", "Custom Target", f"Training objectives for Week {week_number} Day {day_number}", f"Day {day_number}"),
        )
        conn.commit()
        new_row = conn.execute("SELECT * FROM builtin_periodization_days WHERE id=?", (cur.lastrowid,)).fetchone()
        return dict(new_row)
    finally:
        conn.close()


def update_builtin_periodization_exercise(
    exercise_row_id: int,
    name: str,
    muscle: str,
    ex_type: str,
    equip: str,
    target: str,
    sets: int,
    role: str,
) -> dict:
    """Allows updating an exercise in the periodization mesocycle."""
    name = " ".join((name or "").strip().split())
    if not name:
        return {"success": False, "error": "Exercise name is required."}
    conn = get_connection()
    try:
        norm_role = normalize_periodization_role(role)
        norm_type = normalize_periodization_exercise_type(ex_type)
        conn.execute(
            """
            UPDATE builtin_periodization_exercises
            SET exercise_name=?, muscle_group=?, exercise_type=?, equipment=?, target=?, sets=?, role=?
            WHERE id=?
            """,
            (name, muscle.strip(), norm_type, (equip or "").strip() or None, target.strip(), max(1, int(sets)), norm_role, exercise_row_id),
        )
        conn.commit()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def add_builtin_periodization_exercise(
    day_id: int,
    name: str,
    muscle: str,
    ex_type: str,
    equip: str,
    target: str,
    sets: int,
    role: str,
) -> dict:
    """Allows adding a new exercise (Primary Focus, Hypertrophy Support, Compound Auxiliary) to any day of a cycle."""
    name = " ".join((name or "").strip().split())
    if not name:
        return {"success": False, "error": "Exercise name is required."}
    conn = get_connection()
    try:
        norm_role = normalize_periodization_role(role)
        norm_type = normalize_periodization_exercise_type(ex_type)
        max_order = conn.execute(
            "SELECT COALESCE(MAX(order_index), -1) AS max_ord FROM builtin_periodization_exercises WHERE day_id=?",
            (day_id,),
        ).fetchone()["max_ord"]

        cur = conn.execute(
            """
            INSERT INTO builtin_periodization_exercises
            (day_id, exercise_name, muscle_group, exercise_type, equipment, target, sets, role, order_index)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (day_id, name, muscle.strip(), norm_type, (equip or "").strip() or None, target.strip(), max(1, int(sets)), norm_role, max_order + 1),
        )
        conn.commit()
        return {"success": True, "exercise_id": cur.lastrowid}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def delete_builtin_periodization_exercise(exercise_row_id: int) -> bool:
    """Allows Admin to remove an exercise from a day in the built-in periodization cycle."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM builtin_periodization_exercises WHERE id=?", (exercise_row_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def update_builtin_periodization_day(
    day_id: int,
    phase_name: str,
    phase_badge: str,
    objective: str,
) -> dict:
    """Allows Admin to update phase info, badge, and objective for a periodization day."""
    conn = get_connection()
    try:
        conn.execute(
            """
            UPDATE builtin_periodization_days
            SET phase_name=?, phase_badge=?, objective=?
            WHERE id=?
            """,
            (phase_name.strip(), phase_badge.strip(), objective.strip(), day_id),
        )
        conn.commit()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def reset_builtin_periodization_to_default() -> bool:
    """Allows Admin to reset the entire built-in periodization cycle to official default."""
    conn = get_connection()
    try:
        conn.execute("DELETE FROM builtin_periodization_exercises")
        conn.execute("DELETE FROM builtin_periodization_days")
        conn.execute("DELETE FROM builtin_periodization_programs")
        conn.commit()
        seed_builtin_periodization(conn)
        return True
    finally:
        conn.close()


def duplicate_periodization_day_as_routine(
    user_id: int,
    week_num: int,
    day_num: int,
    custom_name: Optional[str] = None,
    program_id: Optional[int] = None,
) -> dict:
    """Clones a day from a periodization mesocycle directly into the user's custom routines."""
    program_map = get_builtin_periodization_program(program_id)
    week_data = program_map.get(week_num)
    if not week_data or day_num not in week_data["days"]:
        return {"success": False, "error": f"Week {week_num} Day {day_num} not found."}

    day_exs = week_data["days"][day_num]
    routine_name = (custom_name or "").strip() or f"Week {week_num} Day {day_num} ({week_data['phase']})"

    conn = get_connection()
    try:
        cur = conn.execute("INSERT INTO routines (user_id, name) VALUES (?, ?)", (user_id, routine_name))
        new_rid = cur.lastrowid

        for idx, item in enumerate(day_exs):
            clean_n = item["name"].strip()
            # Match or create exercise in exercises table
            ex_row = conn.execute(
                "SELECT id FROM exercises WHERE (user_id=? OR user_id IS NULL) AND lower(name)=lower(?) LIMIT 1",
                (user_id, clean_n),
            ).fetchone()
            if ex_row:
                eid = ex_row["id"]
            else:
                cur_e = conn.execute(
                    "INSERT INTO exercises (name, muscle_group, exercise_type, equipment, user_id) VALUES (?, ?, ?, ?, ?)",
                    (clean_n, item["muscle"], item["type"], item.get("equip") or None, user_id),
                )
                eid = cur_e.lastrowid

            conn.execute(
                "INSERT INTO routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                (new_rid, eid, idx),
            )

        conn.commit()
        return {"success": True, "routine_id": new_rid, "name": routine_name}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def duplicate_routine(routine_id: int, user_id: int, new_name: Optional[str] = None) -> dict:
    """Clones any routine (user custom or built-in) into the user's personal routines."""
    conn = get_connection()
    try:
        r_row = conn.execute("SELECT * FROM routines WHERE id=? AND user_id=?", (routine_id, user_id)).fetchone()
        if r_row:
            base_name = r_row["name"]
            ex_rows = conn.execute(
                "SELECT exercise_id, order_index FROM routine_exercises WHERE routine_id=? ORDER BY order_index",
                (routine_id,),
            ).fetchall()
        else:
            b_row = conn.execute("SELECT * FROM builtin_routines WHERE id=?", (routine_id,)).fetchone()
            if not b_row:
                return {"success": False, "error": "Routine not found."}
            base_name = b_row["name"]
            ex_rows = conn.execute(
                "SELECT exercise_id, order_index FROM builtin_routine_exercises WHERE routine_id=? ORDER BY order_index",
                (routine_id,),
            ).fetchall()

        copy_name = (new_name or "").strip() or f"{base_name} (Copy)"
        cur = conn.execute("INSERT INTO routines (user_id, name) VALUES (?, ?)", (user_id, copy_name))
        new_id = cur.lastrowid
        for er in ex_rows:
            conn.execute(
                "INSERT INTO routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                (new_id, er["exercise_id"], er["order_index"]),
            )
        conn.commit()
        return {"success": True, "routine_id": new_id, "name": copy_name}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def update_builtin_routine(routine_id: int, name: str, exercise_ids: list[int]) -> dict:
    """Allows Admin to update an existing built-in routine."""
    name = (name or "").strip()
    if not name:
        return {"success": False, "error": "Routine name is required."}
    if not exercise_ids:
        return {"success": False, "error": "Choose at least one exercise."}
    conn = get_connection()
    try:
        dup = conn.execute("SELECT id FROM builtin_routines WHERE lower(name)=lower(?) AND id != ?", (name, routine_id)).fetchone()
        if dup:
            return {"success": False, "error": "Another built-in routine has this name."}
        conn.execute("UPDATE builtin_routines SET name=? WHERE id=?", (name, routine_id))
        conn.execute("DELETE FROM builtin_routine_exercises WHERE routine_id=?", (routine_id,))
        for idx, eid in enumerate(exercise_ids):
            conn.execute(
                "INSERT INTO builtin_routine_exercises (routine_id, exercise_id, order_index) VALUES (?, ?, ?)",
                (routine_id, eid, idx),
            )
        conn.commit()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()


def update_builtin_exercise(exercise_id: int, name: str, muscle_group: str, exercise_type: str, equipment: str = "") -> dict:
    """Allows Admin to update an existing built-in exercise."""
    name = " ".join((name or "").strip().split())
    muscle_group = muscle_group.strip()
    exercise_type = exercise_type.strip().lower()
    if exercise_type == "reps":
        exercise_type = "weights_reps"
    if not name:
        return {"success": False, "error": "Exercise name is required."}
    if not muscle_group:
        return {"success": False, "error": "Muscle group is required."}
    conn = get_connection()
    try:
        dup = conn.execute(
            "SELECT id FROM exercises WHERE user_id IS NULL AND lower(name)=lower(?) AND id != ?",
            (name, exercise_id),
        ).fetchone()
        if dup:
            return {"success": False, "error": "Another built-in exercise has this name."}
        conn.execute(
            "UPDATE exercises SET name=?, muscle_group=?, exercise_type=?, equipment=? WHERE id=? AND user_id IS NULL",
            (name, muscle_group, exercise_type, equipment.strip() or None, exercise_id),
        )
        conn.commit()
        return {"success": True}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        conn.close()
