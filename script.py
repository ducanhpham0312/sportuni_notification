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
URLS = [
    'https://www.tuni.fi/sportuni/omasivu/?page=selection&lang=en&type=3&area=2&week=0',
    'https://www.tuni.fi/sportuni/omasivu/?page=selection&lang=en&type=3&area=2&week=1'
]
SEARCH_TEXTS = ['17:00 Badminton', '17:30 Badminton', '18:00 Badminton', '18:30 Badminton', '19:00 Badminton', 
                '19:30 Badminton', '20:00 Badminton', '20:30 Badminton', '21:00 Badminton', '21:30 Badminton']  
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO').split(', ')  # Assuming EMAIL_TO is a comma-separated list of emails
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

def check_website():
    all_found_elements = {}
    
    for url in URLS:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        found_elements = []
        for search_text in SEARCH_TEXTS:
            elements = soup.find_all(string=lambda string: string and search_text in string)
            found_elements.extend(elements)
        
        if found_elements:
            all_found_elements[url] = found_elements
    
    if len(all_found_elements):
        notify(all_found_elements)
    else:
        print('No new schedule found.')

def notify(all_found_elements):
    subject = '[Auto] Lịch đánh cầu mới tìm thấy'
    body = 'Vào SportUni đặt lịch đi nè, nhanh không kẻo lỡ:\n\n'
    
    for url, elements in all_found_elements.items():
        body += 'Tuần này:\n' if ('week=0' in url) else 'Tuần sau:\n'
        body += '\n'.join([str(element) for element in elements])
        body += '\n\n'
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['Bcc'] = ', '.join(EMAIL_TO)  # Set the 'Bcc' header with all recipients
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        server.send_message(msg)
        print('Notification sent successfully.')
        
        server.quit()
    except Exception as e:
        print(f'Failed to send notification: {e}')

if __name__ == '__main__':
    check_website()