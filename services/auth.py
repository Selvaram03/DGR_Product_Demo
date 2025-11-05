import streamlit as st
import hashlib

def _hash(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def _load_users():
    """
    Configure users in .streamlit/secrets.toml (recommended):

      [USERS.om]
      name = "O&M User"
      password = "om"        # or provide password_hash instead
      role = "O&M"

      [USERS.crm]
      name = "CRM User"
      password = "crm"
      role = "CRM"

      [USERS.admin]
      name = "Admin User"
      password = "admin"
      role = "Admin"
    """
    users = {}
    if "USERS" in st.secrets:
        for uname, info in st.secrets["USERS"].items():
            pwd_hash = info.get("password_hash") or _hash(info.get("password", ""))
            users[uname] = {
                "name": info.get("name", uname),
                "password_hash": pwd_hash,
                "role": info.get("role", "Client"),
            }
        return users

    # Fallback defaults if no secrets provided
    return {
        "om":    {"name": "O&M User",   "password_hash": _hash("om"),    "role": "O&M"},
        "crm":   {"name": "CRM User",   "password_hash": _hash("crm"),   "role": "CRM"},
        "admin": {"name": "Admin User", "password_hash": _hash("admin"), "role": "Admin"},
    }

def login():
    # Already authed?
    if st.session_state.get("_authed"):
        with st.sidebar:
            if st.button("Logout"):
                for k in ("_authed", "username", "role"):
                    st.session_state.pop(k, None)
                st.experimental_rerun()
        return True

    st.subheader("Login")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in")

    if submitted:
        users = _load_users()
        u = users.get(username)
        if u and _hash(password) == u["password_hash"]:
            st.session_state["_authed"] = True
            st.session_state["username"] = username
            st.session_state["role"] = u["role"]
            st.success(f"Welcome, {u['name']} ({u['role']})")
            st.experimental_rerun()
        else:
            st.error("❌ Incorrect username or password")
            return False

    return st.session_state.get("_authed", False)
