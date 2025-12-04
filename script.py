import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import time
import json 

# Load environment variables from .env file
load_dotenv()

# Configuration
URLS = [
    'https://www.tuni.fi/sportuni/omasivu/?page=selection&lang=en&type=3&area=2&week=0',
    'https://www.tuni.fi/sportuni/omasivu/?page=selection&lang=en&type=3&area=2&week=1'
]
SEARCH_TEXTS = ['16:00 Badminton', '17:00 Badminton', '17:30 Badminton', '18:00 Badminton', '18:30 Badminton', '19:00 Badminton', 
                '19:30 Badminton', '20:00 Badminton', '20:30 Badminton', '21:00 Badminton', '21:30 Badminton']  
EMAIL_FROM = os.getenv('EMAIL_FROM')
EMAIL_TO = os.getenv('EMAIL_TO').split(', ')  # Assuming EMAIL_TO is a comma-separated list of emails
SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

STATE_FILE = 'last_notification.json'

def load_previous_state():
    """Load the previous notification state from a file."""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as file:
            return json.load(file)
    return {}

def save_current_state(state):
    """Save the current notification state to a file."""
    with open(STATE_FILE, 'w') as file:
        json.dump(state, file)

def has_content_changed(current_state, previous_state):
    """Check if the current state differs from the previous state."""
    return current_state != previous_state

def check_website():
    all_found_elements = {}
    options = Options()
    options.add_argument("--headless=new")  # Run in headless mode (no GUI)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    service = Service()
    driver = webdriver.Chrome(service=service, options=options)
    
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
                    
                    # Check for "Book court 1" to "Book court 6" in the new page
                    new_soup = BeautifulSoup(driver.page_source, 'html.parser')
                    courts_found = []
                    for court_num in range(1, 7):
                        if new_soup.find(string=f"Book court {court_num}"):
                            courts_found.append(f"Court {court_num}")
                    
                    if len(courts_found) > 0:
                        court_found = ', '.join(courts_found)
                        # Find the last <li> element with role="heading" before the found element
                        label = new_soup.find('b')
                        if url not in all_found_elements:
                            all_found_elements[url] = []
                        
                        # Check if it's a weekend slot (15:00-17:00) or weekday slot
                        is_weekend_slot = search_text in ['17:00 Badminton', '16:00 Badminton', '18:00 Badminton']
                        is_weekend_day = "Sat" in label.text or "Sun" in label.text
                        
                        # Include weekends only for 15:00-17:00 slots, exclude weekends for other slots
                        if (is_weekend_slot and is_weekend_day) or (not is_weekend_slot and not is_weekend_day):
                            all_found_elements[url].append(f"{label.text} - {court_found}.")
                    
                    # Go back to the original URL
                    driver.back()
                    time.sleep(2)  # Wait for 2 seconds to ensure the page loads completely
                except Exception as e:
                    print(f"Error processing element {search_text}: {e}")
    
    driver.quit()
    
    previous_state = load_previous_state()
    if has_content_changed(all_found_elements, previous_state):
        notify(all_found_elements)
        save_current_state(all_found_elements)
    else:
        print('No new schedule found or content has not changed.')

def notify(all_found_elements):
    if not any(all_found_elements.values()):  # Check if there are no schedules found
        print('No schedules to notify.')
        return

    subject = '[Auto] New badminton schedule available'
    body = 'New schedule found:\n\n'
    
    for url, elements in all_found_elements.items():
        if elements:
            body += 'This week:\n' if ('week=0' in url) else 'Next week:\n'
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