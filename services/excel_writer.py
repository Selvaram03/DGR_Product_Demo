# services/excel_writer.py
from openpyxl import load_workbook
from openpyxl.utils.cell import coordinate_from_string, column_index_from_string
import pandas as pd
import numpy as np
import os

# Map your values to cells (edit to match your template)
CELL_MAP = {
    "date": "B4",
    "customer": "B3",
    "total_daily": "E10",
    "total_mtd": "E11",
    "total_ytd": "E12",
    "plf_percent": "E13",
    "breakdown_hours": "C20",
    "weather": "C21",
    "generation_hours": "C22",
    "operating_hours": "C23",
}

def _is_valid_coord(addr: str) -> bool:
    try:
        col, row = coordinate_from_string(addr)
        _ = column_index_from_string(col)
        return isinstance(row, int) and row > 0
    except Exception:
        return False

def _to_scalar(v):
    """Coerce any pandas/numpy/object into a plain Python scalar or safe string."""
    if v is None:
        return None
    # Unwrap pandas/numpy scalars
    if isinstance(v, (np.generic,)):
        return v.item()
    # Single-value Series/Index -> scalar
    if isinstance(v, (pd.Series, pd.Index)) and v.size == 1:
        return v.iloc[0]
    # DataFrame or multi-value Series/Index -> string (for safety)
    if isinstance(v, (pd.Series, pd.Index, pd.DataFrame, list, tuple, dict, set)):
        return str(v)
    # Ensure str/float/int/bool pass through
    if isinstance(v, (str, float, int, bool)):
        return v
    # last resort
    try:
        return float(v)
    except Exception:
        return str(v)

def write_report_from_template(template_path, out_path, context, inverter_rows):
    """
    context: dict with keys from CELL_MAP
    inverter_rows: list of tuples (name, daily_kwh, monthly_kwh) — plain scalars
    """
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template not found: {template_path}")

    wb = load_workbook(template_path)
    ws = wb.active  # use the first sheet; change to wb[sheetname] if needed

    # Fill header / KPI cells
    for k, cell in CELL_MAP.items():
        if not _is_valid_coord(cell):
            # skip invalid coordinates silently
            continue
        raw = context.get(k, "")
        ws[cell] = _to_scalar(raw)

    # Write inverter table (adjust start row/columns to match your template)
    start_row = 30
    for i, row in enumerate(inverter_rows):
        name, dval, mval = row
        r = start_row + i
        ws[f"A{r}"] = _to_scalar(name)
        ws[f"B{r}"] = _to_scalar(dval)
        ws[f"C{r}"] = _to_scalar(mval)

    # Ensure output folder exists
    out_dir = os.path.dirname(out_path) or "."
    os.makedirs(out_dir, exist_ok=True)

    wb.save(out_path)
    return out_path
