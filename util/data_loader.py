# util/data_loader.py
import streamlit as st
from pymongo import MongoClient
import pandas as pd
from datetime import datetime, date

# --- App-level settings ---
# Put MONGO_URI in .streamlit/secrets.toml
MONGO_URI = st.secrets["MONGO_URI"]
DATABASE_NAME = "scada_db"  # per your instruction

# Map customers -> Mongo collections (edit as needed or move to secrets)
CUSTOMERS = ["Imagica", "Caspro"]
COLLECTION_MAP = {
    "Imagica":"opcua_data",
    "Caspro": "Caspro"
}

def list_customers():
    # If provided in secrets, use that instead
    return st.secrets.get("CUSTOMERS", CUSTOMERS)

def _collection_for(customer: str) -> str:
    cmap = st.secrets.get("CUSTOMER_COLLECTIONS", COLLECTION_MAP)
    return cmap.get(customer, customer.lower() + "_data")

def mongo():
    client = MongoClient(MONGO_URI)
    return client[DATABASE_NAME]

# -------------------------------------------------------------------
# YOUR EXACT PIPELINE (wrapped as a function + safe export)
# -------------------------------------------------------------------
def fetch_cleaned_data(collection_name: str, start_date_str: str, end_date_str: str, customer: str = None):
    """
    Fetch documents for the [start_date, end_date] window (inclusive by day).
    start_date_str / end_date_str are in '%d-%b-%Y' format (e.g., '01-Nov-2025').
    """
    start_date = datetime.strptime(start_date_str, "%d-%b-%Y").strftime("%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%d-%b-%Y").strftime("%Y-%m-%d")

    client = MongoClient(MONGO_URI)
    coll = client[DATABASE_NAME][collection_name]

    pipeline = [
        {"$match": {"timestamp": {"$exists": True, "$ne": None}}},
        {
            "$addFields": {
                "ts": {
                    "$switch": {
                        "branches": [
                            {  # Proper ISODate stored as BSON date
                                "case": {"$eq": [{"$type": "$timestamp"}, "date"]},
                                "then": "$timestamp"
                            },
                            {  # 'YYYY-MM-DD HH:MM' string format
                                "case": {
                                    "$and": [
                                        {"$eq": [{"$type": "$timestamp"}, "string"]},
                                        {"$regexMatch": {
                                            "input": "$timestamp",
                                            "regex": "^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}$"
                                        }}
                                    ]
                                },
                                "then": {
                                    "$dateFromString": {
                                        "dateString": "$timestamp",
                                        "format": "%Y-%m-%d %H:%M"
                                    }
                                }
                            },
                        ],
                        "default": None
                    }
                }
            }
        },
        {"$match": {"ts": {"$ne": None}}},
        {"$addFields": {"day": {"$dateToString": {"date": "$ts", "format": "%Y-%m-%d"}}}},
        {"$match": {"day": {"$gte": start_date, "$lte": end_date}}},
        {"$limit": 200000}  # safety limit
    ]

    raw_data = list(coll.aggregate(pipeline, allowDiskUse=True))
    df = pd.DataFrame(raw_data)

    # Local sort (no memory pressure on Mongo)
    if "ts" in df.columns:
        df = df.sort_values("ts")

    client.close()
    return df

# Convenience wrapper used by pages to get a date-window as a DataFrame
def load_period(customer: str, start: date, end: date) -> pd.DataFrame:
    """
    Calls fetch_cleaned_data() with the required %d-%b-%Y strings.
    """
    coll_name = _collection_for(customer)
    start_str = start.strftime("%d-%b-%Y")  # e.g., 01-Nov-2025
    end_str   = end.strftime("%d-%b-%Y")
    df = fetch_cleaned_data(coll_name, start_str, end_str, customer)
    # ensure a uniform day string & date
    if "day" in df.columns:
        df["day_str"] = df["day"].astype(str)
        df["day_dt"] = pd.to_datetime(df["day_str"]).dt.date
    elif "ts" in df.columns:
        df["day_dt"] = pd.to_datetime(df["ts"]).dt.date
        df["day_str"] = pd.to_datetime(df["ts"]).dt.strftime("%Y-%m-%d")
    else:
        # fallback: try any date-like field
        for c in df.columns:
            if "date" in c.lower() or "day" in c.lower():
                df["day_dt"] = pd.to_datetime(df[c]).dt.date
                df["day_str"] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d")
                break
    return df.reset_index(drop=True)
