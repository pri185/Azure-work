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
msg = EmailMessage()
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
