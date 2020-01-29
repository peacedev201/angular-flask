from flask import Flask
from flask_mail import Mail, Message
import os

app = Flask(__name__)

mail_settings = {
    "MAIL_SERVER": 'smtp.gmail.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": "testpeopledb@gmail.com",#"os.environ['EMAIL_USER'],
    "MAIL_PASSWORD": "Pa$$word123"#os.environ['EMAIL_PASSWORD']
}

app.config.update(mail_settings)
mail = Mail(app)

if __name__ == '__main__':
    with app.app_context():
        msg = Message(subject="Congratulation!",
                      sender=app.config.get("MAIL_USERNAME"),
                      recipients=["limike126@gmail.com"], # replace with your email for testing
                      body="Your request was approved! Please login again.")
        mail.send(msg)