# pages/2_Report_Builder.py
import streamlit as st
import pandas as pd
from datetime import date
from util.data_loader import list_customers, load_period, mongo
from util.agg import detect_inverters, daily_monthly_ytd, calc_kpis
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

with st.spinner("Loading data..."):
    df_daily = load_period(customer, data_day, data_day)
    df_mtd   = load_period(customer, month_start, data_day)
    df_ytd   = load_period(customer, ytd_start, data_day)

if df_daily.empty:
    st.error("❌ No data found for selected date")
    st.stop()

inv_cols, irr_col = detect_inverters(df_daily)

final_df, daily_gen, mtd_gen, ytd_gen, di, mi = daily_monthly_ytd(
    df_daily, df_mtd, df_ytd, inv_cols, irr_col, customer
)

kpi = calc_kpis(customer, daily_gen, mtd_gen)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Daily Generation (kWh)", f"{kpi['total_daily']:.2f}")
c2.metric("MTD Generation (kWh)", f"{kpi['total_mtd']:.2f}")
c3.metric("YTD Generation (kWh)", f"{ytd_gen.sum():.2f}")
c4.metric("PLF (%)", f"{kpi['plf_percent']:.2f}")

st.subheader("Inverter-wise Summary")
st.dataframe(final_df, use_container_width=True)

omi = mongo()["dgr_manual_inputs"].find_one({"customer": customer, "day": str(data_day)}) or {}

out_dir = "exports"
os.makedirs(out_dir, exist_ok=True)
file_path = os.path.join(out_dir, f"{customer}_DGR_{data_day}.xlsx")

ctx = {
    "date": str(data_day),
    "customer": customer,
    "total_daily": float(kpi["total_daily"]),
    "total_mtd": float(kpi["total_mtd"]),
    "total_ytd": float(ytd_gen.sum()),
    "plf_percent": f"{kpi['plf_percent']:.2f}%",
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
    write_report_from_template("data/Energy report template.xlsx", file_path, ctx, inv_rows)
    st.success("✅ Excel generated")
    with open(file_path, "rb") as f:
        st.download_button("Download Report", f, file_path)

if colB.button("Save Draft for CRM"):
    db = mongo()
    db["dgr_reports"].update_one(
        {"customer": customer, "day": str(data_day)},
        {"$set": {
            "customer": customer,
            "day": str(data_day),
            "kpis": {
                "daily": float(kpi['total_daily']),
                "mtd": float(kpi['total_mtd']),
                "ytd": float(ytd_gen.sum()),
                "plf": float(kpi['plf_percent'])
            },
            "file_path": file_path,
            "status": "draft"
        }},
        upsert=True
    )
    st.success("💾 Draft saved")
