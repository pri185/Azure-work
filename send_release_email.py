import os
import smtplib
import subprocess
import re
from datetime import datetime
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

# 🔹 Increment patch version (expects format vX.Y.Z)
def increment_version(tag):
    match = re.match(r"^v(\d+)\.(\d+)\.(\d+)$", tag)
    if match:
        major, minor, patch = map(int, match.groups())
        patch += 1
        new_version = f"v{major}.{minor}.{patch}"
        print(f"⬆️ Incremented version: {new_version}")
        return new_version
    else:
        print("⚠️ Invalid tag format, defaulting to v1.0.0")
        return "v1.0.0"

# 🔹 Check if tag exists locally or remotely
def tag_exists(tag):
    try:
        subprocess.run(['git', 'rev-parse', tag], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# 🔹 Tag the new release and push it if tag does not exist
def tag_and_push(tag):
    if tag_exists(tag):
        print(f"⚠️ Tag {tag} already exists. Skipping tagging.")
        return
    try:
        subprocess.run(['git', 'tag', tag], check=True)
        subprocess.run(['git', 'push', 'origin', tag], check=True)
        print(f"✅ Created and pushed tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git tagging failed: {e}")

# 🔹 Read content from .docx file (unchanged, just read)
def read_docx(file_path):
    try:
        doc = Document(file_path)
        content = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        print("📄 Read release note content from DOCX.")
        return content if content else "(No content found in release note.)"
    except Exception as e:
        print(f"❌ Failed to read DOCX: {e}")
        return "(Error reading release note.)"

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

    release_date = datetime.now().strftime("%Y-%m-%d")
    intro = f"<b>📦 Version:</b> {tag}<br><b>🗓️ Release Date:</b> {release_date}<br><br>"
    full_body = intro + content.replace("\n", "<br>")

    msg = EmailMessage()
    msg['Subject'] = f"📢 Website Release Note - {tag}"
    msg['From'] = sender
    msg['To'] = ", ".join(to_emails)
    if cc_emails:
        msg['Cc'] = ", ".join(cc_emails)

    all_recipients = to_emails + cc_emails + bcc_emails
    msg.set_content(full_body, subtype='html')

    try:
        with open(docx_path, 'rb') as f:
            msg.add_attachment(f.read(),
                               maintype='application',
                               subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
                               filename=os.path.basename(docx_path))
        print("📎 Attached .docx file.")
    except Exception as e:
        print(f"❌ Failed to attach DOCX: {e}")

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
    new_tag = increment_version(latest_tag)
    tag_and_push(new_tag)
    content = read_docx(DOCX_PATH)
    send_email_with_release(new_tag, content, DOCX_PATH)
