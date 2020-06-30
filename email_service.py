# Import smtplib for the actual sending function
import smtplib
# Import the email modules we'll need
from email.message import EmailMessage


class EmailService():

    def sendEmail(self,content):
        msg = EmailMessage()
        msg.set_content(content)

        # me == the sender's email address
        # you == the recipient's email address
        msg['Subject'] = 'New found compnay'
        msg['From'] = 'xinchunlanus@163.com'
        msg['To'] = 'xinchunlanus@163.com'

        # Send the message via our own SMTP server.
        s = smtplib.SMTP_SSL('smtp.163.com', 465)
        s.login('xinchunlanus@163.com','Abcdef123456')

        s.send_message(msg)
        s.quit()
