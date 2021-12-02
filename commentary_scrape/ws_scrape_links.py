import os
import utils
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from seleniumrequests import Firefox
from selenium.webdriver.support.ui import WebDriverWait

# CONSTANTS
LINK_FILE = '../data/game_links.csv'
TEXT_DIR = '../data/text/'

def last_page():
    nav_tag = cmmnt_bttn = utils.find_css_element(driver, 'div[class="page-info"]')
    page_soup = BeautifulSoup(nav_tag.get_attribute('outerHTML'), 'html')
    current_page = page_soup.select_one('span[class="current-page"]').text
    total_pages = page_soup.select_one('span[class="total-pages"]').text
    if int(current_page) < int(total_pages):
        return False
    else:
        return True

def scrape_page():
    global cmmnt_df
    cmmnt_box = utils.find_css_element(driver, 'ul[class="commentary-items"]')
    # comment_soup = BeautifulSoup(cmmnt_box.get_attribute('outerHTML'), 'html')
    comment_soup = BeautifulSoup(driver.page_source, 'html')
    cmmnt_items = comment_soup.select('li[class="commentary-item"]')
    for cmmnt_tag in cmmnt_items:
        comment = cmmnt_tag.select_one('span[class="commentary-text"]').text
        row = cmmnt_tag.attrs
        row['comment'] = comment
        del row['class']
        cmmnt_df = cmmnt_df.append(row, ignore_index=True)

def is_captcha():
    try:
        driver.switch_to_frame('main-iframe')
        _ = driver.find_element_by_css_selector('div[class="captcha"]')
        driver.switch_to_default_content()
        return True
    except:
        return False

# MAIN
# set up driver
profile = os.getenv('GECKO_PROFILE_PATH')
driver_path = os.getenv('GECKO_DRIVER_PATH')
driver = Firefox(webdriver.FirefoxProfile(profile), executable_path=driver_path)
driver.wait = WebDriverWait(driver, timeout=15, poll_frequency=1.5)

df = utils.get_links_data(LINK_FILE)
for index, row in df.iterrows():
    if 'scraped' in row:
        if not pd.isnull(row['scraped']):
            print('skipping match {} {}'.format(row['name'], row['season']))
            continue

    driver.get(row['link'].replace('MatchReport', 'Live'))
    utils.sleep(3, 5)

    if is_captcha():
        input('solve captcha. press any key to continue')

    cmmnt_bttn = utils.find_css_element(driver, 'a[href*=match-commentary]')
    cmmnt_bttn.click()
    utils.sleep()

    cmmnt_df = pd.DataFrame()
    while not last_page():
        scrape_page()

        next_bttn = utils.find_css_element(driver, 'span[data-page*="next-page"]')
        next_bttn.click()
        utils.sleep(3, 5)

    scrape_page()

    # write out file, record
    str_date = pd.to_datetime(row['date']).strftime('%Y%m%d')
    filename = '{}_{}_{}.txt'.format(row['name'], row['season'], str_date)
    cmmnt_df.drop_duplicates(inplace=True)
    cmmnt_df.to_csv(TEXT_DIR + filename, encoding='utf-16', index=False, sep='\t')
    print('file written {}'.format(filename))
    df.loc[index, 'scraped'] = 'x'

df.to_csv(LINK_FILE, index=False)
