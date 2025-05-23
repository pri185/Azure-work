import smtplib
from email.message import EmailMessage
from docx import Document

# Read content from docx
def read_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Email settings
EMAIL_SENDER = 'gpps0618@gmail.com'
EMAIL_PASSWORD = 'ndgf miva kgch kzyf'
EMAIL_RECEIVER = 'yamini1599singh@gmail.com'

# Read release note content
docx_file_path = "Website_Release_Note.docx"
content = read_docx(docx_file_path)

# Prepare email
msg = EmailMessage()import os
import subprocess
import smtplib
from email.message import EmailMessage

# 🔹 Get the latest Git tag (release version)
def get_latest_release_tag():
    try:
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).strip().decode()
        return tag
    except subprocess.CalledProcessError:
        return "No tag found"

# 🔹 Compose email
def send_release_email():
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")

    release_tag = get_latest_release_tag()

    msg = EmailMessage()
    msg["Subject"] = f"New Release: {release_tag}"
    msg["From"] = sender
    msg["To"] = receiver

    msg.set_content(f"""
    Hello,

    A new release ({release_tag}) has been pushed to the repository.

    Best regards,
    Release Bot
    """)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("Release email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")

# 🔹 Run it
if __name__ == "__main__":
    send_release_email()

msg['Subject'] = 'Website Release Note - Version 1.2.0'
msg['From'] = EMAIL_SENDER
msg['To'] = EMAIL_RECEIVER
msg.set_content(content)

# Attach the .docx file
with open(docx_file_path, 'rb') as f:
    file_data = f.read()
    file_name = f.name
    msg.add_attachment(file_data, maintype='application',
                       subtype='vnd.openxmlformats-officedocument.wordprocessingml.document',
                       filename=file_name)

# Send email
with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
    smtp.send_message(msg)

print("Email sent successfully!")
