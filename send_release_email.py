import os
import smtplib
import subprocess
import re
import html
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from docx import Document

# 🔹 Get the latest release tag or initialize to v1.0.0
def get_latest_release_tag():
    try:
        subprocess.run(['git', 'fetch', '--tags'], check=True)
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).strip().decode()
        print(f"🔍 Latest Git tag found: {tag}")
        return tag
    except subprocess.CalledProcessError:
        print("⚠️ No tags found, starting from v1.0.0")
        return "v1.0.0"

# 🔹 Check if tag exists locally or remotely
def tag_exists(tag):
    try:
        subprocess.run(['git', 'rev-parse', tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# 🔹 Increment patch version until unused tag is found
def increment_version_until_free(latest_tag):
    match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", latest_tag)
    if not match:
        print("⚠️ Invalid tag format, defaulting to v1.0.0")
        return "v1.0.0"
    major, minor, patch = map(int, match.groups())

    while True:
        patch += 1
        new_tag = f"v{major}.{minor}.{patch}"
        if not tag_exists(new_tag):
            print(f"⬆️ New version available: {new_tag}")
            return new_tag
        else:
            print(f"⚠️ Tag {new_tag} already exists. Trying next patch...")

# 🔹 Tag the new release and push it
def tag_and_push(tag):
    try:
        subprocess.run(['git', 'tag', tag], check=True)
        subprocess.run(['git', 'push', 'origin', tag], check=True)
        print(f"✅ Created and pushed tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git tagging failed: {e}")

# 🔹 Read content from .docx file
def read_docx(file_path):
    try:
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        print("📄 Read release note content from DOCX.")
        return content if content else "(No content found in release note.)"
    except Exception as e:
        print(f"❌ Failed to read DOCX: {e}")
        return "(Error reading release note.)"

# 🔹 Get DOCX file's last modified time formatted in IST
def get_docx_modification_time(docx_path):
    mod_timestamp = os.path.getmtime(docx_path)
    mod_datetime_utc = datetime.fromtimestamp(mod_timestamp, tz=timezone.utc)
    IST_OFFSET = timedelta(hours=5, minutes=30)
    mod_datetime_ist = mod_datetime_utc + IST_OFFSET
    return mod_datetime_ist.strftime("%Y-%m-%d %H:%M IST")

# 🔹 Send email with release note, dynamic version and date in subject/body, and attach unchanged DOCX
def send_email_with_release(tag, content, docx_path):
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    receivers = os.getenv("EMAIL_RECEIVER", "")
    cc_list = os.getenv("EMAIL_CC", "")
    bcc_list = os.getenv("EMAIL_BCC", "")

    to_emails = [email.strip() for email in receivers.split(',') if email.strip()]
    cc_emails = [email.strip() for email in cc_list.split(',') if email.strip()]
    bcc_emails = [email.strip() for email in bcc_list.split(',') if email.strip()]

    if not sender or not password or not to_emails:
        print("❌ Missing required environment variables: EMAIL_SENDER, EMAIL_PASSWORD, EMAIL_RECEIVER")
        return

    release_date = get_docx_modification_time(docx_path)
    intro = f"<b>📦 Version:</b> {tag}<br><b>🗓️ Release Date:</b> {release_date}<br><br>"
    safe_content = html.escape(content).replace("\n", "<br>")
    full_body = intro + safe_content

    msg = EmailMessage()
    msg['Subject'] = f"📢 Website Release Note - {tag}"
    msg['From'] = sender
    msg['To'] = ", ".join(to_emails)
    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)

    all_recipients = to_emails + cc_emails + bcc_emails

    # Plain text fallback
    msg.set_content("This is an HTML email. Please view it in an HTML-compatible email client.")

    # Add HTML version
    msg.add_alternative(full_body, subtype='html')

    # Attach DOCX
    try:
        with open(docx_path, 'rb') as f:
            msg.add_attachment(f.read(),
                               maintype='application',
                               subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
                               filename=os.path.basename(docx_path))
        print("📎 Attached .docx file.")
    except Exception as e:
        print(f"❌ Failed to attach DOCX: {e}")

    # Send Email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg, to_addrs=all_recipients)
        print(f"✅ Email sent to: {', '.join(all_recipients)}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

# 🔹 Main
if __name__ == "__main__":
    DOCX_PATH = "Website_Release_Note.docx"
    latest_tag = get_latest_release_tag()
    new_tag = increment_version_until_free(latest_tag)
    tag_and_push(new_tag)
    content = read_docx(DOCX_PATH)
    send_email_with_release(new_tag, content, DOCX_PATH)
