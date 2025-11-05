import smtplib, ssl, os
from email.message import EmailMessage

def send_report_email(to_addrs, subject, body, attachment):
    if not os.path.exists(attachment): return False

    msg = EmailMessage()
    msg["Subject"]=subject
    msg["From"]="no-reply@company.com"
    msg["To"]=", ".join(to_addrs)
    msg.set_content(body)

    with open(attachment,"rb") as f:
        msg.add_attachment(f.read(), maintype="application",
        subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=os.path.basename(attachment))

    with smtplib.SMTP("localhost",25) as s:
        s.send_message(msg)
    return True