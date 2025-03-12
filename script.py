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
# SEARCH_TEXTS = ['19:00 Badminton', '20:00 Badminton', '21:00 Badminton', '20:30 Badminton', 
#                 '21:30 Badminton', '17:00 Badminton', '18:00 Badminton']  
SEARCH_TEXTS = ['07:00 Badminton', '08:00 Badminton', '09:00 Badminton']
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO').split(',')  # Assuming EMAIL_TO is a comma-separated list of emails
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

def check_website():
    response = requests.get(URL)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    found_elements = []
    for search_text in SEARCH_TEXTS:
        elements = soup.find_all(text=lambda text: text and search_text in text)
        found_elements.extend(elements)
    
    if found_elements:
        notify(found_elements)

def notify(elements):
    subject = '[Auto] Lịch đánh cầu mới tìm thấy'
    body = 'Vào SportUni đặt lịch đi nè, nhanh không kẻo lỡ:\n\n'
    body += '\n'.join([str(element) for element in elements])
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        for email in EMAIL_TO:
            msg['To'] = email
            server.sendmail(EMAIL_FROM, email, msg.as_string())
        
        server.quit()
        print('Notification sent successfully.')
    except Exception as e:
        print(f'Failed to send notification: {e}')

if __name__ == '__main__':
    check_website()