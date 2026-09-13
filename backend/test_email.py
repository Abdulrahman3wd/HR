from app.email_service import send_email

result = send_email(
    to_email="abdoorchida@gmail.com",
    subject="Test Email from HR Agent",
    html_body="<h1>It works!</h1><p>SMTP is configured correctly.</p>"
)

print("Success!" if result else "Failed.")