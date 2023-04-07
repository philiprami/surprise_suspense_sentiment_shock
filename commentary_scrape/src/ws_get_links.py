import os
import utils
from bs4 import BeautifulSoup
from selenium import webdriver
# from seleniumrequests import Firefox
from selenium.webdriver.support.ui import WebDriverWait

# CONSTANTS
LINK_FILE = '../data/game_links.csv'
SEASON_CODES = {'2020' : '8055',
                '2019' : '7609',
                '2018' : '7172'}

SEASON_CODES = {'2018' : '7172'}

# MAIN
# set up driver
# profile = os.getenv('GECKO_PROFILE_PATH')
driver_path = os.getenv('GECKO_DRIVER_PATH')
# driver = Firefox(webdriver.FirefoxProfile(profile), executable_path=driver_path)
driver = webdriver.Firefox(executable_path=driver_path)
driver.wait = WebDriverWait(driver, timeout=15, poll_frequency=1.5)

df = utils.get_links_data(LINK_FILE)
for season in SEASON_CODES:
    code = SEASON_CODES[season]
    link = 'https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/{}/England-Premier-League'.format(code)
    driver.get(link)
    utils.sleep(3, 5)

    week_bttn = utils.find_css_element(driver, 'a[class*="date button"]')
    week = week_bttn.text
    while (df['week'] == week).sum() == 0:
        soup = BeautifulSoup(driver.page_source, 'html')
        table = soup.select_one('div[id="tournament-fixture"] > tbody')
        tags = table.select('tr')

        date = None
        for tag in tags:
            name_tag = ' '.join(tag.attrs['class'])
            if name_tag == 'rowgroupheader':
                date = tag.text
                print('date found {}'.format(date))
            else:
                time = tag.select_one('td[class="time"]').text
                home_team = tag.select_one('td[class*="team home"]').text
                away_team = tag.select_one('td[class*="team away"]').text
                matchup = '{}-{}'.format(home_team, away_team)
                link_tag = tag.select_one('a[class*="match-link"]')
                link = 'https://www.whoscored.com' + link_tag.attrs['href']
                row = {'week' : week,
                       'date' : date,
                       'time' : time,
                       'link' : link,
                       'name' : matchup,
                       'season' : season}

                df = df.append(row, ignore_index=True)
                print(row)

        # iterate previous week
        prev_bttn = utils.find_css_element(driver, 'a[class*="previous button"]')
        if 'is-disabled' in prev_bttn.get_attribute('class'):
            break

        prev_bttn.click()
        utils.sleep()

        week_bttn = utils.find_css_element(driver, 'a[class*="date button"]')
        week = week_bttn.text

df.to_csv(LINK_FILE, index=False)
