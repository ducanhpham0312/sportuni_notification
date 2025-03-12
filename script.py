import os
import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
URL = 'https://www.tuni.fi/sportuni/omasivu/?page=selection&lang=en&type=3&area=2&week=0'
SEARCH_TEXT = '19:00 Badminton'
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO')
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

def check_website():
    response = requests.get(URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Find elements containing the specific text
    elements = soup.find_all(text=lambda text: text and SEARCH_TEXT in text)
    
    if elements:
        notify(elements)

def notify(elements):
    subject = 'New HTML Element Found'
    body = f'New HTML elements containing "{SEARCH_TEXT}" were found:\n\n'
    body += '\n'.join([str(element) for element in elements])
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        server.quit()
        print('Notification sent successfully.')
    except Exception as e:
        print(f'Failed to send notification: {e}')

if __name__ == '__main__':
    check_website()