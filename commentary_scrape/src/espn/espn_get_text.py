import os
import time
import glob
import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from seleniumrequests import Firefox
from selenium.common import exceptions
from selenium.webdriver.support.ui import WebDriverWait

LINK_FILE = '../data/game_links.csv'
TEXT_DIR = '../data/text/'
TEXT_FILES = glob.glob(TEXT_DIR + '*')

def sleep(x=1, y=3.5, step=0.5):
    secs = np.random.choice(np.arange(x, y, step))
    time.sleep(secs)

def is_stale(element, mult=False):
    try:
        element.tag_name
    except exceptions.StaleElementReferenceException:
        return True
    except:
        pass

    return False

def find_css_element(css_selector):
    wait.until(lambda x: x.find_element_by_css_selector(css_selector))
    element = driver.find_element_by_css_selector(css_selector)
    if is_stale(element):
        driver.refresh()
        sleep()
        find_css_element(css_selector)

    return element

# set up driver
profile = os.getenv('GECKO_PROFILE_PATH')
driver_path = os.getenv('GECKO_DRIVER_PATH')
driver = Firefox(webdriver.FirefoxProfile(profile), executable_path=driver_path)
wait = WebDriverWait(driver, timeout=15, poll_frequency=1.5)

df = pd.read_csv(LINK_FILE)
for index, row in df.iterrows():
    driver.get(row['link'])
    sleep()

    commentary_bttn = find_css_element('a[name*="fullcommentary"]')
    commentary_bttn.click()
    sleep(3, 5)

    table = find_css_element('div[id*="match-commentary"]')
    tbl_soup = BeautifulSoup(table.get_attribute('innerHTML').strip(), 'html')
    cmmnt_tags = tbl_soup.select('tr[data-id*=comment-]')
    for c_tag in reversed(cmmnt_tags):
        time_tag = c_tag.select_one('td[class="time-stamp"]')
        gametime = time_tag.text


    break
