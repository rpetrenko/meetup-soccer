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
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def find_element_by_css_selector(driver, value):
    return driver.find_element(by=By.CSS_SELECTOR, value=value)


def meetup_login(driver, username, password):
    css_email = "#email"
    css_passw = "#current-password"
    css_submit = "button[data-testid=submit]"
    logout_id = "logout-link"
    start_new_group = "start-new-group-link"
    url_login = "https://www.meetup.com/login"

    driver.get(url_login)
    find_element_by_css_selector(driver, css_email).send_keys(username)
    find_element_by_css_selector(driver, css_passw).send_keys(password)
    find_element_by_css_selector(driver, css_submit).click()
   
    logout = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, start_new_group))
    )
    print("logged in")


def rsvp_now(driver, mail_html_file):
    driver.get("file://{}".format(mail_html_file))
    css_rsvp_now = ".button-learn-more"
    css_rsvp_submit = ".rsvp-submitButton"

    find_element_by_css_selector(driver, css_rsvp_now).click()
    print("opened RSVP meetup page")

    find_element_by_css_selector(driver, css_rsvp_submit).click()
    print("RSVP'ed")


def meetup_auto_rsvp(meetup_creds, local_html, headless=True, wait=10):
    with open(meetup_creds, 'r') as fh:
        data = json.load(fh)
        username = data['username']
        password = data['password']
    assert username, "no meetup username"
    assert password, "no meetup password"
    assert os.path.exists(local_html), "no local html found"
    
    curdir = os.getcwd()
    driver_path = os.path.join(curdir, "drivers/geckodriver")
    options = Options()
    options.headless = headless
    driver = webdriver.Firefox(options=options, executable_path=driver_path)

    driver.implicitly_wait(wait)

    try:
        meetup_login(driver, username, password)
        rsvp_now(driver, local_html)
    except Exception as e:
        print(e)
        return e
    finally:
        time.sleep(10)
        driver.quit()
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <meetup_creds_file> <local_html_file>")
        exit(1)
          
    meetup_creds = sys.argv[1]
    local_html = sys.argv[2]
    meetup_auto_rsvp(meetup_creds, local_html, headless=False)
