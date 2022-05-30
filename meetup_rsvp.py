"""
Gmail:
1. create label: soccer
2. automatically place all meetup soccer events to that label
3. on client read emails from soccer folder and RSVP

Selenium notes:
download gecko driver for firefox:
https://github.com/mozilla/geckodriver/releases
"""

from enum import unique
import os
import time
import sys
import json
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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
        self.skip_events = set()

        
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

    def is_in_not_going(self, href):
        css_avatar_person = ".avatar--person"
        css_not_going = ".response-filter-no"
        self.driver.get(href)
        time.sleep(10)
        
        # click not going
        self.find_element_by_css_selector(css_not_going).click()
        time.sleep(2)

        els = self.find_elements_by_css_selector(css_avatar_person)
        # if we found ourselves in Not going list, there will be two same avatars
        # one from the list at one from top right corner after login
        unique_names = set(el.text for el in els)
        return len(els) != len(unique_names)

    def rsvp_to_events(self, url_events):
        done = False
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
            if meetup_date_str in self.skip_events:
                continue
            print(f"====Parsing {meetup_date_str}")
            fmt = '%a, %b %d, %Y, %I:%M %p %Z'
            event_date = datetime.strptime(meetup_date_str, fmt)
            today = datetime.today()
            delta = event_date - today
            days_ahead = delta.days
            if days_ahead > 7:
                print("...more than 7 days ahead")
                continue
            
            if attendees and int(attendees[i].text.split()[0]) <= 2:
                print("...not opened yet")
                continue

            response_text = responses[i].text
            if response_text == "Going":
                print("...already going")
            elif response_text == "Waitlist":
                print("...oh well, waitlisted")
            else:
                href = links[i].get_attribute("href")
                print("...checking if in Not going list")
                not_going = self.is_in_not_going(f"{href}/attendees/")
                if not_going:
                    print(f"...found yourself in Not going list")
                    self.skip_events.add(meetup_date_str)
                else:
                    print(f"RSVP to: {meetup_date_str}")
                    print(f"...{href}")
                    res = self.rsvp_to_event(links[i], href)
                    if res:
                        self.skip_events.add(meetup_date_str)
                return False
        done = True
        return done

    def rsvp_to_event(self, link, href):
        """
        
        return True on succeess
        """
        css_attend = "button[data-testid=attend-irl-btn]"
        css_submit = "button[data-event-label=event-question-modal-confirm]"
        link_text = link.text

        try:
            self.driver.get(href)
            time.sleep(10)
            el = self.find_element_by_css_selector(css_attend)
            if el:
                print(f"...clicking attend button for [{link_text}]")
                el.click()
                time.sleep(10)
                print(f"...clicking submit button")
                el = self.find_element_by_css_selector(css_submit)
                el.click()
                time.sleep(10)
                return True
            else:
                print("ERROR: attend button not found")
        except Exception as e:
            print(e)
        return False


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
        count = 20
        for i in range(count):
            if meetup.rsvp_to_events(events_url):
                break
            time.sleep(10)

    finally:
        meetup.driver.quit()