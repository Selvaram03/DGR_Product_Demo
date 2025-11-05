import streamlit as st
import hashlib
import json
from typing import Dict, Any

# optional bcrypt support (only if you want to use bcrypt hashes)
try:
    from passlib.hash import bcrypt
    _HAS_BCRYPT = True
except Exception:
    _HAS_BCRYPT = False

def _sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _load_users() -> Dict[str, Dict[str, Any]]:
    """
    Reads users from Streamlit Secrets:
      - Set a key named `USERS_JSON` in Streamlit Cloud Secrets (UI).
      - Value format (JSON string):
        {
          "om":    {"name":"O&M User","role":"O&M","password":"om"},
          "crm":   {"name":"CRM User","role":"CRM","password_hash":"<sha256-or-bcrypt>"},
          "admin": {"name":"Admin User","role":"Admin","password":"admin"}
        }

      Supported credentials per user:
        - "password": plaintext
        - "password_hash": sha256 hex (64 chars) OR bcrypt ($2a$/$2b$/$2y$)
    """
    if "USERS_JSON" in st.secrets and st.secrets["USERS_JSON"]:
        try:
            parsed = json.loads(st.secrets["USERS_JSON"])
            assert isinstance(parsed, dict)
            # normalize minimal fields
            users = {}
            for uname, info in parsed.items():
                users[uname] = {
                    "name": info.get("name", uname),
                    "role": info.get("role", "Client"),
                    "password": info.get("password"),
                    "password_hash": info.get("password_hash"),
                }
            return users
        except Exception as e:
            st.error(f"Invalid USERS_JSON in Secrets: {e}")

    # Fallback demo users for local runs if no secrets set
    return {
        "om":    {"name": "O&M User",   "role": "O&M",   "password": "om",    "password_hash": None},
        "crm":   {"name": "CRM User",   "role": "CRM",   "password": "crm",   "password_hash": None},
        "admin": {"name": "Admin User", "role": "Admin", "password": "admin", "password_hash": None},
    }

def _verify(user: Dict[str, Any], candidate: str) -> (bool, str):
    plain = user.get("password")
    phash = user.get("password_hash")

    # plaintext
    if isinstance(plain, str) and plain != "":
        return (candidate == plain, "plaintext")

    # sha256 hex (64 chars)
    if isinstance(phash, str) and len(phash) == 64 and all(c in "0123456789abcdef" for c in phash.lower()):
        return (_sha256_hex(candidate) == phash.lower(), "sha256")

    # bcrypt
    if isinstance(phash, str) and phash.startswith(("$2a$", "$2b$", "$2y$")):
        if not _HAS_BCRYPT:
            return (False, "bcrypt-missing-passlib")
        try:
            return (bcrypt.verify(candidate, phash), "bcrypt")
        except Exception:
            return (False, "bcrypt-error")

    return (False, "no-credential")

def login() -> bool:
    # Already authed?
    if st.session_state.get("_authed"):
        with st.sidebar:
            st.success(f"Logged in as {st.session_state['username']} ({st.session_state['role']})")
            if st.button("Logout"):
                for k in ("_authed", "username", "role"):
                    st.session_state.pop(k, None)
                st.rerun()
        return True

    st.subheader("Login")

    # Optional debug: shows which usernames were loaded + credential mode
    with st.expander("Debug (temporary)"):
        dbg = _load_users()
        lines = []
        for u, info in dbg.items():
            mode = "plaintext" if info.get("password") else (
                   "sha256" if isinstance(info.get("password_hash"), str) and len(info["password_hash"]) == 64 else
                   "bcrypt" if isinstance(info.get("password_hash"), str) and info["password_hash"].startswith(("$2a$","$2b$","$2y$")) else
                   "UNSET")
            lines.append(f"- {u}: {mode}")
        st.code("Users loaded:\n" + "\n".join(lines))

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        users = _load_users()
        u = users.get(username)
        if not u:
            st.error("❌ Incorrect username or password")
            return False

        ok, mode = _verify(u, password)
        if ok:
            st.session_state["_authed"] = True
            st.session_state["username"] = username
            st.session_state["role"] = u.get("role", "Client")
            st.success(f"Welcome, {u.get('name', username)} ({st.session_state['role']})")
            st.rerun()
        else:
            if mode == "bcrypt-missing-passlib":
                st.error("❌ 'passlib[bcrypt]' not installed but bcrypt hash provided. Run: pip install passlib[bcrypt]")
            elif mode == "no-credential":
                st.error("❌ No password or password_hash configured for this user in Secrets.")
            else:
                st.error("❌ Incorrect username or password")
            return False

    return st.session_state.get("_authed", False)
