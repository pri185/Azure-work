import os
import subprocess
import smtplib
from email.message import EmailMessage
import re

def get_latest_release_tag():
    try:
        # Get the latest tag
        tag = subprocess.check_output(['git', 'describe', '--tags', '--abbrev=0']).strip().decode()
        return tag
    except subprocess.CalledProcessError:
        # No tag found, start at v1.0.0
        return "v1.0.0"

def increment_version(tag):
    match = re.match(r"v(\d+)\.(\d+)\.(\d+)", tag)
    if match:
        major, minor, patch = map(int, match.groups())
        patch += 1  # Increment patch version
        return f"v{major}.{minor}.{patch}"
    return "v1.0.0"

def send_release_email(tag):
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD")
    receiver = os.environ.get("EMAIL_RECEIVER")

    msg = EmailMessage()
    msg["Subject"] = f"🚀 New Release: {tag}"
    msg["From"] = sender
    msg["To"] = receiver

    msg.set_content(f"""
    Hello,

    A new release ({tag}) has been generated and deployed.

    Best regards,
    Release Bot
    """)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender, password)
            smtp.send_message(msg)
        print("✅ Email sent successfully.")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

def tag_and_push(tag):
    try:
        subprocess.run(['git', 'tag', tag], check=True)
        subprocess.run(['git', 'push', 'origin', tag], check=True)
        print(f"✅ Created and pushed tag: {tag}")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to tag or push: {e}")

if __name__ == "__main__":
    latest_tag = get_latest_release_tag()
    new_tag = increment_version(latest_tag)
    tag_and_push(new_tag)
    send_release_email(new_tag)
