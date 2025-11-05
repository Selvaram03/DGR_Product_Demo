from openpyxl import load_workbook
import os

CELL_MAP = {
 "date":"B4","customer":"B3","total_daily":"E10","total_mtd":"E11",
 "total_ytd":"E12","plf_percent":"E13",
 "breakdown_hours":"C20","weather":"C21","generation_hours":"C22","operating_hours":"C23"
}

def write_report_from_template(template,out,ctx,inv_rows):
    wb = load_workbook(template)
    ws = wb.active

    for k,v in CELL_MAP.items():
        ws[v] = ctx.get(k,"")

    start=30
    for i,(inv,d,m) in enumerate(inv_rows):
        r=start+i
        ws[f"A{r}"]=inv; ws[f"B{r}"]=float(d); ws[f"C{r}"]=float(m)

    os.makedirs(os.path.dirname(out),exist_ok=True)
    wb.save(out)
