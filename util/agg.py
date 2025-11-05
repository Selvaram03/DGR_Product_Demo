import pandas as pd

PLF_BASE = {
    "Imagica": 3.06,
    "PGCIL": 26.56,
    "TMD": 10,
    "BEL2": 20,
    "Caspro": 3.05,
    "Dunung": 3.08,
    "Kasturi": 3.00,
    "Paranjape": 2.11,
    "Mauryaa": 3.08,
    "Vinathi_3": 3.00,
    "Vinathi_4": 3.07,
    "BEL1": 10.00,
    "Vinathi_2": 25.00
}

CUSTOMER_INVERTERS = {
    "Imagica": 18,
    "BEL2": 1,
    "BEL1": 1,
    "Caspro": 11,
    "Dunung": 13,
    "Kasturi": 23,
    "Mauryaa": 13,
    "Paranjape": 19,
    "Vinathi_3": 25,
    "Vinathi_4": 15,
    "TMD": 9,
    "PGCIL": 32,
    "Vinathi_2": 2
}

def detect_inverters(df):
    cols=[c for c in df.columns if "inv" in c.lower()]
    return cols,"Irradiation" if "Irradiation" in df.columns else None

def daily_monthly_ytd(d, m, y, inv, irr, cust):
    dg = d[inv].sum()
    mg = m[inv].sum()
    yg = y[inv].sum()

    final=pd.DataFrame({
        "Inverter":inv,
        "Daily Generation (kWh)":d[inv].sum(),
        "Monthly Generation (kWh)":m[inv].sum()
    })

    return final, dg, mg, yg, None, None

def calc_kpis(cust, daily, monthly):
    total = daily.sum()
    num_inverters = CUSTOMER_INVERTERS[cust]
    plf_base = PLF_BASE[cust]
    # Avoid division by zero
    denom = 24 * plf_base * num_inverters if (plf_base and num_inverters) else 1
    plf = (total / denom)
    return {"total_daily":total,"total_mtd":monthly.sum(),"plf_percent":plf}
