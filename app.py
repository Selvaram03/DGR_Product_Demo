import streamlit as st
from services.auth import login

st.set_page_config(page_title="DGR Suite", page_icon="⚡", layout="wide")

if "_authed" not in st.session_state:
    st.session_state["_authed"] = False

if not st.session_state["_authed"]:
    if login():
        st.session_state["_authed"] = True
        st.experimental_rerun()
    else:
        st.stop()
