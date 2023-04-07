import os
import time
import numpy as np
import pandas as pd
from selenium.common import exceptions
from selenium.webdriver.common.by import By

def sleep(x=1, y=3.5, step=0.5):
    secs = np.random.choice(np.arange(x, y, step))
    time.sleep(secs)

def get_links_data(filename):
    if os.path.isfile(filename):
        df = pd.read_csv(filename)
    else:
        df = pd.DataFrame(columns=['week', 'date', 'time', 'link', 'name', 'season'])
    return df

def is_stale(element):
    try:
        element.tag_name
    except exceptions.StaleElementReferenceException:
        return True
    except:
        pass

    return False

def find_css_element(driver, css_selector):
    driver.wait.until(lambda x: x.find_element_by_css_selector(css_selector))
    element = driver.find_element_by_css_selector(css_selector)
    if is_stale(element):
        driver.refresh()
        sleep()
        find_css_element(css_selector)

    return element

def find_css_element(driver, selector):
    by = By.CSS_SELECTOR
    try:
        element = driver.find_element(by, selector)
    except exceptions.NoSuchElementException:
        return None

    if element:
        if is_stale(element):
            driver.refresh()
            time.sleep(3)
            find_css_element(driver, selector)

    return element