"""HTN authentication with persistent browser login and multi-layer session recovery."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import Optional

import extra_streamlit_components as stx
import streamlit as st

from db.database import get_connection, get_user, init_db

USERNAME_PATTERN = re.compile(r"^[A-Za-z!@#$%^&*()_+\-=[\]{};:'\",.<>/?\\|`~]+$")
PBKDF2_ITERATIONS = 200_000
AUTH_COOKIE_NAME = "htn_auth_token"
AUTH_COOKIE_DAYS = 30
COOKIE_KEY = "htn_auth_cookie_manager"
SESSION_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "db", ".htn_session")


def _cookie_manager():
    return stx.CookieManager(key=COOKIE_KEY)


def _ensure_auth_sessions_table():
    conn = get_connection()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS auth_sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )"""
        )
        conn.commit()
    finally:
        conn.close()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _now_utc():
    return datetime.now(timezone.utc)


def _parse_expiry(value: str):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def validate_username(username: str) -> Optional[str]:
    username = (username or "").strip()
    if not username:
        return "Username is required."
    if any(ch.isspace() for ch in username):
        return "Username cannot contain spaces."
    if any(ch.isdigit() for ch in username):
        return "Username cannot contain numbers."
    if not USERNAME_PATTERN.fullmatch(username):
        return "Username can contain letters and special characters only."
    return None


def validate_password(password: str) -> Optional[str]:
    return "Password must be at least 6 characters." if len(password or "") < 6 else None


def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    if stored.startswith("pbkdf2_sha256$"):
        try:
            _, iterations_text, salt_hex, digest_hex = stored.split("$", 3)
            actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations_text))
            return hmac.compare_digest(actual, bytes.fromhex(digest_hex))
        except (ValueError, TypeError):
            return False
    return hmac.compare_digest(hashlib.sha256(password.encode("utf-8")).hexdigest(), stored)


def _local_email_for_username(username: str) -> str:
    return f"htn-{hashlib.sha256(username.casefold().encode('utf-8')).hexdigest()}@local.htn"


def register_auth_user(username: str, password: str) -> dict:
    init_db()
    _ensure_auth_sessions_table()
    username = (username or "").strip()
    err = validate_username(username)
    if err:
        return {"success": False, "error": err}
    err = validate_password(password)
    if err:
        return {"success": False, "error": err}

    conn = get_connection()
    try:
        if conn.execute("SELECT 1 FROM users WHERE username COLLATE NOCASE=? LIMIT 1", (username,)).fetchone():
            return {"success": False, "error": "Username already exists."}
        cur = conn.execute(
            "INSERT INTO users (username,email,password,display_name,handle) VALUES (?,?,?,?,?)",
            (username, _local_email_for_username(username), _hash_password(password), username, username),
        )
        conn.commit()
        return {"success": True, "user_id": cur.lastrowid}
    except sqlite3.IntegrityError:
        return {"success": False, "error": "Username already exists."}
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> dict:
    init_db()
    _ensure_auth_sessions_table()
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username COLLATE NOCASE=? LIMIT 1", ((username or "").strip(),)
        ).fetchone()
    finally:
        conn.close()

    if not row or not _verify_password(password or "", row["password"]):
        return {"success": False, "error": "Invalid username or password."}
    return {"success": True, "user": dict(row)}


def _get_persisted_token() -> Optional[str]:
    """Retrieve the session token across local cache, URL params, or cookies."""
    # 1. Native Streamlit request headers / cookies (instant and synchronous)
    try:
        if hasattr(st, "context") and hasattr(st.context, "cookies"):
            cookie_val = st.context.cookies.get(AUTH_COOKIE_NAME)
            if cookie_val:
                return str(cookie_val)
    except Exception:
        pass

    # 2. Local disk session file
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                token = data.get("token")
                if token:
                    return str(token)
        except Exception:
            pass

    # 3. Streamlit query parameters
    try:
        q_token = st.query_params.get("auth")
        if q_token:
            return str(q_token)
    except Exception:
        pass

    # 4. Asynchronous Cookie Manager fallback
    try:
        c_token = _cookie_manager().get(AUTH_COOKIE_NAME)
        if c_token:
            return str(c_token)
    except Exception:
        pass

    return None


def _clear_persisted_token():
    """Wipes all persistence stores on logout or expiration."""
    try:
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    except Exception:
        pass

    try:
        if "auth" in st.query_params:
            del st.query_params["auth"]
    except Exception:
        pass

    try:
        _cookie_manager().delete(AUTH_COOKIE_NAME, key="delete_auth_token")
    except Exception:
        pass


def restore_login() -> Optional[dict]:
    # Fast path: user ID already authenticated in active session_state
    uid = st.session_state.get("auth_user_id")
    if uid:
        user = get_user(int(uid))
        if user:
            st.session_state.user = user
            st.session_state.theme_pref = user.get("theme_pref") or "Original"
            return user
        st.session_state.pop("auth_user_id", None)
        st.session_state.pop("auth_username", None)

    init_db()
    _ensure_auth_sessions_table()

    token = _get_persisted_token()
    if not token:
        return None

    th = _hash_token(str(token))
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT user_id, expires_at FROM auth_sessions WHERE token_hash=?", (th,)
        ).fetchone()
        if not row:
            _clear_persisted_token()
            return None

        try:
            exp = _parse_expiry(row["expires_at"])
        except ValueError:
            exp = _now_utc() - timedelta(seconds=1)

        if exp <= _now_utc():
            conn.execute("DELETE FROM auth_sessions WHERE token_hash=?", (th,))
            conn.commit()
            _clear_persisted_token()
            return None

        user = get_user(int(row["user_id"]))
        if not user:
            _clear_persisted_token()
            return None

        # Restore session state & URL parameter
        st.session_state.auth_user_id = int(user["id"])
        st.session_state.auth_username = user["username"]
        st.session_state.user = user
        st.session_state.theme_pref = user.get("theme_pref") or "Original"
        try:
            st.query_params["auth"] = str(token)
        except Exception:
            pass
        return user
    finally:
        conn.close()


def log_in(user: dict) -> None:
    init_db()
    _ensure_auth_sessions_table()
    token = secrets.token_urlsafe(32)
    th = _hash_token(token)
    exp = _now_utc() + timedelta(days=AUTH_COOKIE_DAYS)
    uid = int(user["id"])

    conn = get_connection()
    try:
        conn.execute("DELETE FROM auth_sessions WHERE user_id=?", (uid,))
        conn.execute(
            "INSERT INTO auth_sessions(token_hash, user_id, expires_at) VALUES(?, ?, ?)",
            (th, uid, exp.isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    # 1. Synchronously persist to disk session cache
    try:
        os.makedirs(os.path.dirname(SESSION_FILE), exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump({"token": token, "user_id": uid}, f)
    except Exception:
        pass

    # 2. Persist to URL query params
    try:
        st.query_params["auth"] = token
    except Exception:
        pass

    # 3. Set browser cookie
    try:
        _cookie_manager().set(
            AUTH_COOKIE_NAME,
            token,
            key="set_auth_token",
            path="/",
            max_age=AUTH_COOKIE_DAYS * 86400,
            secure=False,
            same_site="lax",
        )
    except Exception:
        pass

    st.session_state.auth_user_id = uid
    st.session_state.auth_username = user["username"]
    st.session_state.user = user
    st.session_state.theme_pref = user.get("theme_pref") or "Original"


def log_out() -> None:
    init_db()
    _ensure_auth_sessions_table()
    token = _get_persisted_token()
    if token:
        conn = get_connection()
        try:
            conn.execute("DELETE FROM auth_sessions WHERE token_hash=?", (_hash_token(str(token)),))
            conn.commit()
        finally:
            conn.close()

    _clear_persisted_token()

    for k in ("auth_user_id", "auth_username", "htn_coach_messages", "_auth_checked"):
        st.session_state.pop(k, None)

    st.switch_page("pages/login.py")


def current_user() -> Optional[dict]:
    return restore_login()


def require_login() -> dict:
    user = restore_login()
    if user:
        return user
    st.switch_page("pages/login.py")
    raise RuntimeError("Redirecting to login")