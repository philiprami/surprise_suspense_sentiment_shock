import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

while True:
    try:
        driver = webdriver.Firefox(webdriver.FirefoxProfile(os.getenv('GECKO_PROFILE_PATH')),
          executable_path=os.getenv('GECKO_DRIVER_PATH'))
        wait = WebDriverWait(self.driver, timeout=15, poll_frequency=1.5)
        break
    except exceptions.WebDriverException:
        sleep()
        continue
    except:
        break

soup = BeautifulSoup(driver.page_source, 'lxml')


'https://www.bbc.com/sport/football/37604054'

https://push.api.bbci.co.uk/p?t=morph%3A%2F%2Fdata%2Fbbc-morph-sport-filter-data-provider-priority-order-football-scores%2Ftournament%2Fpremier-league%2Fversion%2F2.2.8&c=1

https://push.api.bbci.co.uk/p?t=morph%3A%2F%2Fdata%2Fbbc-morph-sport-football-scores-filter-priority-order-data%2Ftournament%2Fpremier-league%2Fversion%2F2.1.8&c=1

https://push.api.bbci.co.uk/p?t=morph%3A%2F%2Fdata%2Fbbc-morph-sport-football-scores-filter-priority-order-data%2Ftournament%2Fpremier-league%2Fversion%2F2.1.8&c=10

link = '''
https://push.api.bbci.co.uk/b?t=%2Fdata%2Fbbc-morph-football-scores-match-list-data%2FendDate%2F2018-01-31%2FstartDate%2F2018-01-01%2FtodayDate%2F2020-01-28%2Ftournament%2Fpremier-league%2Fversion%2F2.4.1?timeout=5
'''
response = requests.get(link)
data = response.json()


%2FstartTime%2F2020-01-22T19:30:00+00:00
