import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

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
    driver = webdriver.Chrome()  # Make sure you have the ChromeDriver installed and in your PATH
    
    for url in URLS:
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        for search_text in SEARCH_TEXTS:
            elements = driver.find_elements(By.XPATH, f"//*[contains(text(), '{search_text}')]")
            for element in elements:
                try:
                    element.click()
                    
                    # Wait for 5 seconds for the new page to load
                    time.sleep(2)
                    
                    # Check for "Book court 2" or "Book court 5" in the new page
                    new_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    courts_found = []
                    if new_soup.find(string="Book court 2"):
                        courts_found.append("Court 2")
                    if new_soup.find(string="Book court 5"):
                        courts_found.append("Court 5")
                    
                    if len(courts_found) > 0:
                        court_found = ', '.join(courts_found)
                        # Find the last <li> element with role="heading" before the found element
                        label = new_soup.find('b')
                        if url not in all_found_elements:
                            all_found_elements[url] = []
                        all_found_elements[url].append(f"{label.text} - {court_found} found.")
                    
                    # Go back to the original URL
                    driver.back()
                    time.sleep(2)  # Wait for 2 seconds to ensure the page loads completely
                except Exception as e:
                    print(f"Error processing element {search_text}: {e}")
    
    driver.quit()
    
    if len(all_found_elements):
        notify(all_found_elements)
    else:
        print('No new schedule found.')

def notify(all_found_elements):
    subject = '[Auto] New badminton schedule available'
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
        
        server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print('Notification sent successfully.')
        
        server.quit()
    except Exception as e:
        print(f'Failed to send notification: {e}')

if __name__ == '__main__':
    check_website()