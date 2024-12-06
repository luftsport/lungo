# coding=utf-8
import smtplib
import email.message
import email.utils
from ext.app.decorators import _async
from ext.scf import EMAIL, SEND_EMAIL


@_async
def send_email(recepient, subject, message, priority='2'):
    if SEND_EMAIL is True:
        msg = email.message.Message()
        msg['From'] = 'notifications@nlf.no'
        msg['To'] = recepient
        msg['Subject'] = "{}".format(subject)
        msg.add_header('Content-Type', 'text')
        msg.set_payload(message)
        msg['X-Priority'] = priority
        s = smtplib.SMTP(EMAIL['smtp'], EMAIL['smtp_port'])
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.sendmail(msg['From'], [msg['To']], msg.as_string().encode('utf-8'))
        s.quit()
    else:
        print(f'DID NOT SEND EMAIL, config is set to {SEND_EMAIL}')
        print('[EMAIL]')
        print(message)
