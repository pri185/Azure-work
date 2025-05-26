import os
import smtplib
import subprocess
import re
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from docx import Document

def get_latest_release_tag():
    try:
        subprocess.run(['git', 'fetch', '--tags'], check=True)
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).strip().decode()
        return tag
    except subprocess.CalledProcessError:
        return "v1.0.0"

def increment_version(tag):
    match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", tag)
    if match:
        major, minor, patch = map(int, match.groups())
        patch += 1
        return f"v{major}.{minor}.{patch}"
    else:
        return "v1.0.0"

def tag_exists(tag):
    try:
        subprocess.run(['git', 'rev-parse', tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def tag_and_push(tag):
    if tag_exists(tag):
        print(f"Tag {tag} already exists, skipping.")
        return
    subprocess.run(['git', 'tag', tag], check=True)
    subprocess.run(['git', 'push', 'origin', tag], check=True)
    print(f"Tagged and pushed {tag}")

def read_docx_content(path):
    doc = Document(path)
    content = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
    return content if content else "(No release note content.)"

def get_docx_mod_time_ist(path):
    ts = os.path.getmtime(path)
    utc_dt = datetime.fromtimestamp(ts, timezone.utc)
    ist_dt = utc_dt + timedelta(hours=5, minutes=30)
    return ist_dt.strftime("%Y-%m-%d %H:%M IST")

def send_email(tag, content, docx_path):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receivers = os.getenv("EMAIL_RECEIVER", "")
    cc_list = os.getenv("EMAIL_CC", "")
    bcc_list = os.getenv("EMAIL_BCC", "")

    to_emails = [e.strip() for e in receivers.split(',') if e.strip()]
    cc_emails = [e.strip() for e in cc_list.split(',') if e.strip()]
    bcc_emails = [e.strip() for e in bcc_list.split(',') if e.strip()]

    if not sender or not password or not to_emails:
        print("Missing EMAIL_SENDER, EMAIL_PASSWORD or EMAIL_RECEIVER environment variables")
        return

    release_date = get_docx_mod_time_ist(docx_path)
    body_html = f"<b>📦 Version:</b> {tag}<br><b>🗓️ Release Date:</b> {release_date}<br><br>" + content.replace("\n", "<br>")

    msg = EmailMessage()
    msg['Subject'] = f"📢 Website Release Note - {tag}"
    msg['From'] = sender
    msg['To'] = ", ".join(to_emails)
    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)

    all_recipients = to_emails + cc_emails + bcc_emails
    msg.set_content(body_html, subtype='html')

    with open(docx_path, 'rb') as f:
        msg.add_attachment(f.read(),
                           maintype='application',
                           subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
                           filename=os.path.basename(docx_path))

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(sender, password)
        smtp.send_message(msg, to_addrs=all_recipients)
    print(f"Email sent to {', '.join(all_recipients)}")

if __name__ == "__main__":
    DOCX_PATH = "Website_Release_Note.docx"
    latest_tag = get_latest_release_tag()
    new_tag = increment_version(latest_tag)
    tag_and_push(new_tag)
    content = read_docx_content(DOCX_PATH)
    send_email(new_tag, content, DOCX_PATH)
