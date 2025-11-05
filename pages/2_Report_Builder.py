# pages/2_Report_Builder.py
import streamlit as st
import pandas as pd
from datetime import date
from util.data_loader import list_customers, load_period, mongo
from util.agg import clean_dataframe, get_daily_monthly_yearly_data, calculate_kpis
from services.excel_writer import write_report_from_template
import os

st.set_page_config(page_title="DGR Builder", page_icon="📊", layout="wide")

if st.session_state.get("role") not in ["O&M", "CRM", "Admin"]:
    st.error("Access Denied")
    st.stop()

st.title("📊 Generate Daily Generation Report")

customer = st.selectbox("Customer", list_customers())
report_date = st.date_input("Report Date", value=date.today())
data_day = (pd.to_datetime(report_date) - pd.Timedelta(days=1)).date()

month_start = data_day.replace(day=1)
ytd_start = data_day.replace(month=1, day=1)
st.caption(f"Data day: **{data_day}** · Month start: **{month_start}** · YTD start: **{ytd_start}**")

with st.spinner("Loading data..."):
    # Load YTD window (covers daily & MTD windows too)
    df_ytd_full = load_period(customer, ytd_start, data_day)

if df_ytd_full.empty:
    st.warning("No data found for the selected customer/day.")
    st.stop()

# Clean + detect using your logic
df_clean, inverter_cols, irradiation_col = clean_dataframe(df_ytd_full.copy(), customer)

# Compute Daily / MTD / YTD using your core
final_df, daily_gen, monthly_gen, ytd_gen, daily_irr, monthly_avg_irr = get_daily_monthly_yearly_data(
    df_clean, inverter_cols, report_date, irradiation_col, customer
)

# KPIs (daily, monthly, PLF, yearly)
total_daily, total_mtd, plf_percent, total_ytd = calculate_kpis(customer, daily_gen, monthly_gen, ytd_gen)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Daily (kWh)", f"{total_daily:.2f}")
c2.metric("MTD (kWh)", f"{total_mtd:.2f}")
c3.metric("YTD (kWh)", f"{total_ytd:.2f}")
c4.metric("PLF (%)", f"{plf_percent:.2f}")

st.subheader("Inverter-wise Summary")
st.dataframe(final_df, use_container_width=True)

# Pull O&M manual inputs
omi = mongo()["dgr_manual_inputs"].find_one({"customer": customer, "day": str(data_day)}) or {}

# Excel export via template (already has total_ytd mapping)
out_dir = "exports"
os.makedirs(out_dir, exist_ok=True)
file_path = os.path.join(out_dir, f"{customer}_DGR_{data_day}.xlsx")

ctx = {
    "date": str(data_day),
    "customer": customer,
    "total_daily": float(total_daily),
    "total_mtd": float(total_mtd),
    "total_ytd": float(total_ytd),
    "plf_percent": f"{plf_percent:.2f}%",
    "breakdown_hours": omi.get("breakdown_hours", 0),
    "weather": omi.get("weather", ""),
    "generation_hours": omi.get("generation_hours", 0),
    "operating_hours": omi.get("operating_hours", 0),
}

inv_rows = list(zip(
    final_df["Inverter"],
    final_df["Daily Generation (kWh)"],
    final_df["Monthly Generation (kWh)"],
))

colA, colB = st.columns(2)
if colA.button("Generate Excel Report"):
    out_file = write_report_from_template("data/Energy report template.xlsx", file_path, ctx, inv_rows)
    st.success(f"✅ Excel exported: {out_file}")
    with open(out_file, "rb") as f:
        st.download_button("Download Report", f, os.path.basename(out_file))

if colB.button("Save Draft for CRM"):
    db = mongo()
    db["dgr_reports"].update_one(
        {"customer": customer, "day": str(data_day)},
        {"$set": {
            "customer": customer,
            "day": str(data_day),
            "kpis": {
                "daily": float(total_daily),
                "mtd": float(total_mtd),
                "ytd": float(total_ytd),
                "plf": float(plf_percent)
            },
            "file_path": file_path,
            "status": "draft"
        }},
        upsert=True
    )
    st.success("💾 Draft saved")
