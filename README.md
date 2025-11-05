⚡ DGR (Daily Generation Report) System

A complete Daily Generation Reporting Suite for Solar/O&M operations powered by Streamlit, MongoDB, and Excel automation.

This system enables:

✅ Secure login with user roles (Admin / CRM / O&M / Client)
✅ O&M daily inputs (Breakdown Hours, Weather, Gen/Operating hours)
✅ Automated DGR report generation
✅ Daily, Monthly & YTD generation calculation
✅ Excel report export using template
✅ CRM approval workflow
✅ Email trigger to clients after approval
✅ Multi-plant support
✅ On-prem Windows server deployment supported

🎯 Features
| Module               | Features                                               |
| -------------------- | ------------------------------------------------------ |
| Login & Roles        | Secure login, Role-based access (Admin/CRM/O&M/Client) |
| O&M Inputs           | Breakdown hours, generation hours, weather logs        |
| Data Aggregation     | Daily, MTD, YTD + PLF                                  |
| Report Builder       | Plant-wise DGR, inverter table, Excel export           |
| CRM Portal           | Approve, lock & email report to clients                |
| Mongo DB Integration | Reads SCADA logs, supports string timestamps           |
| Excel Engine         | Fills template & downloads .xlsx                       |
| Email System         | Auto-mail reports to configured customers              |

📂 Project Structure
DGR_App/
│── app.py
│── requirements.txt
│── README.md
│── data/
│   └── Energy report template.xlsx
│── services/
│   ├── auth.py
│   ├── mailer.py
│   └── excel_writer.py
│── util/
│   ├── data_loader.py
│   └── agg.py
└── pages/
    ├── 1_O&M_Inputs.py
    ├── 2_Report_Builder.py
    └── 3_CRM_Approvals.py
