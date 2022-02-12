"""
Gmail:
1. create label: soccer
2. automatically place all meetup soccer events to that label
3. on client read emails from soccer folder and RSVP

Selenium notes:
download gecko driver for firefox:
https://github.com/mozilla/geckodriver/releases
"""

import os
import time
import sys
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


class MeetupRSVP(object):
    def __init__(self, headless=False) -> None:
        curdir = os.getcwd()
        driver_path = os.path.join(curdir, "drivers/geckodriver")
        options = Options()
        options.headless = headless
        self.driver = webdriver.Firefox(options=options, executable_path=driver_path)
        self.driver.implicitly_wait(10)

        
    def find_element_by_css_selector(self, value):
        try:
            return self.driver.find_element(by=By.CSS_SELECTOR, value=value)
        except NoSuchElementException as e:
            return None

        
    def find_elements_by_css_selector(self, value):
        return self.driver.find_elements(by=By.CSS_SELECTOR, value=value)


    def login(self, username, password):
        css_email = "#email"
        css_passw = "#current-password"
        css_submit = "button[data-testid=submit]"
        logout_id = "logout-link"
        start_new_group = "start-new-group-link"
        url_login = "https://www.meetup.com/login"

        self.driver.get(url_login)
        self.find_element_by_css_selector(css_email).send_keys(username)
        self.find_element_by_css_selector(css_passw).send_keys(password)
        self.find_element_by_css_selector(css_submit).click()
    
        logout = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, start_new_group))
        )
        print("logged in")

    def rsvp_to_events(self, url_events):
        css_header = ".eventCardHead"
        css_attendees = ".avatarRow--attendingCount"
        css_link = ".eventCard--link"
        css_response = ".eventCard--clickable"
        self.driver.get(url_events)
        
        headers = self.find_elements_by_css_selector(css_header)
        attendees = self.find_elements_by_css_selector(css_attendees)
        links = self.find_elements_by_css_selector(css_link)
        responses = self.find_elements_by_css_selector(css_response)

        for i, header in enumerate(headers):
            meetup_date_str = header.text.splitlines()[0]
            print(f"====Parsing {meetup_date_str}")
            fmt = '%a, %b %d, %Y, %I:%M %p %Z'
            event_date = datetime.strptime(meetup_date_str, fmt)
            today = datetime.today()
            delta = event_date - today
            days_ahead = delta.days
            if days_ahead > 7:
                print("...more than 7 days ahead")
                return False
            
            if attendees and int(attendees[i].text.split()[0]) <= 2:
                print("...not opened yet")
                continue

            response_text = responses[i].text
            if response_text == "Going":
                print("...already going")
            elif response_text == "Waitlist":
                print("...oh well, waitlisted")
            else:
                print(f"RSVP to: {meetup_date_str}")
                return self.rsvp_to_event(links[i])
        return False

    def rsvp_to_event(self, link):
        css_attend = "button[data-e2e=event-footer--attend-btn]"
        link_text = link.text

        try:
            link.click()
            time.sleep(15)
            el = self.find_element_by_css_selector(css_attend)
            if el:
                print(f"clicking attend button for [{link_text}]")
                el.click()
                print("attending")
                time.sleep(15)
                return True
        except Exception as e:
            print(e)
        return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <meetup_creds_file> <events_url>")
        exit(1)   
    meetup_creds = os.path.expanduser(sys.argv[1])
    events_url = sys.argv[2]
    headless = True

    with open(meetup_creds, 'r') as fh:
        data = json.load(fh)
        username = data['username']
        password = data['password']
    assert username, "no meetup username"
    assert password, "no meetup password"
    
    meetup = MeetupRSVP(headless=headless)

    try:
        meetup.login(username, password)
        while True:
            res = meetup.rsvp_to_events(events_url)
            if not res:
                break
    finally:
        time.sleep(10)
        meetup.driver.quit()