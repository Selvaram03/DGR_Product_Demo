import streamlit as st
import hashlib

st.set_page_config(page_title="Mini Login", page_icon="🔐")

def _hash(p: str) -> str:
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

USERS = {
    "om":    {"name": "O&M User",   "password_hash": _hash("om"),    "role": "O&M"},
    "crm":   {"name": "CRM User",   "password_hash": _hash("crm"),   "role": "CRM"},
    "admin": {"name": "Admin User", "password_hash": _hash("admin"), "role": "Admin"},
}

def login():
    # already authed?
    if st.session_state.get("_authed"):
        st.sidebar.success(f"Logged in as {st.session_state['username']} ({st.session_state['role']})")
        if st.sidebar.button("Logout"):
            for k in ("_authed", "username", "role"):
                st.session_state.pop(k, None)
            st.rerun()
        return True

    st.header("🔐 Login")
    with st.form("login_form", clear_on_submit=False):
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        submit = st.form_submit_button("Sign in")

    if submit:
        user = USERS.get(u)
        if user and _hash(p) == user["password_hash"]:
            st.session_state["_authed"] = True
            st.session_state["username"] = u
            st.session_state["role"] = user["role"]
            st.success("✅ Authenticated, reloading…")
            st.rerun()
        else:
            st.error("❌ Incorrect username or password")
            return False

    return st.session_state.get("_authed", False)

if "_authed" not in st.session_state:
    st.session_state["_authed"] = False

if not st.session_state["_authed"]:
    if login():
        st.rerun()
    else:
        st.stop()

st.success("🎉 You are in!")
st.write("Protected content goes here.")
