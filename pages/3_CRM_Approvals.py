import streamlit as st
from util.data_loader import mongo
from services.mailer import send_report_email

st.set_page_config(page_title="CRM Approval", page_icon="✅")

if st.session_state.get("role") not in ["CRM", "Admin"]:
    st.error("Access Denied")
    st.stop()

st.title("✅ Approve & Send Reports")

db = mongo()
recs = list(db["dgr_reports"].find().sort("day", -1))

for r in recs:
    with st.expander(f"{r['customer']} | {r['day']} | {r['status']}"):
        st.json(r)
        to = st.text_input("Send Email To", value="customer@mail.com")

        if st.button(f"Approve_{r['_id']}"):
            db["dgr_reports"].update_one({"_id": r["_id"]},{"$set":{"status":"approved"}})
            st.success("Approved ✅")

        if st.button(f"Send_{r['_id']}"):
            send_report_email([to], "DGR Report", "Find report attached", r["file_path"])
            st.success("📧 Sent successfully")
