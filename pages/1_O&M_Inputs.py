import streamlit as st
from datetime import date
from util.data_loader import mongo, list_customers

st.set_page_config(page_title="O&M Inputs", page_icon="🛠️", layout="wide")

if st.session_state.get("role") not in ["O&M", "Admin"]:
    st.error("Access Denied")
    st.stop()

st.title("🛠️ O&M Daily Inputs Form")
customer = st.selectbox("Customer", list_customers())
day = st.date_input("Data Day", value=date.today())

c1, c2 = st.columns(2)
breakdown = c1.number_input("Breakdown Hours", min_value=0.0, step=0.5)
weather = c2.text_input("Weather Condition")

c3, c4 = st.columns(2)
gen_hours = c3.number_input("Generation Hours", min_value=0.0, step=0.5)
op_hours = c4.number_input("Operating Hours", min_value=0.0, step=0.5)

notes = st.text_area("Remarks (Optional)")

if st.button("Save"):
    db = mongo()
    coll = db["dgr_manual_inputs"]
    coll.update_one(
        {"customer": customer, "day": str(day)},
        {"$set": {
            "customer": customer,
            "day": str(day),
            "breakdown_hours": breakdown,
            "weather": weather,
            "generation_hours": gen_hours,
            "operating_hours": op_hours,
            "notes": notes,
            "user": st.session_state.get("username")
        }},
        upsert=True
    )
    st.success("✅ Saved successfully")
