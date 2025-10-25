from __future__ import annotations
import os, smtplib
from email.mime.text import MIMEText
from utils import read_textfile, today_pl_date

def send_latest(html_path: str, subject_prefix: str):
    host = os.getenv("SMTP_HOST")
    port = int(os.getenv("SMTP_PORT","587"))
    user = os.getenv("SMTP_USER")
    pwd  = os.getenv("SMTP_PASS")
    from_addr = os.getenv("SMTP_FROM") or user
    if not (host and user and pwd):
        print("SMTP not configured; skipping.")
        return
    subs = read_textfile("data/subscribers.txt")
    if not subs:
        print("No subscribers; skipping.")
        return
    html = open(html_path, "r", encoding="utf-8").read()
    msg = MIMEText(html, "html", "utf-8")
    msg["Subject"] = f"{subject_prefix} {today_pl_date()}"
    msg["From"] = from_addr
    msg["To"] = ", ".join(subs)
    with smtplib.SMTP(host, port) as s:
        s.starttls()
        s.login(user, pwd)
        s.sendmail(from_addr, subs, msg.as_string())
