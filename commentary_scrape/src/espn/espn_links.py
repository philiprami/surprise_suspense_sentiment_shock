import os
import sys
import time
import requests
import datetime
import numpy as np
import pandas as pd
# from selenium import webdriver
# from seleniumrequests import Firefox

# profile = os.getenv('GECKO_PROFILE_PATH')
# driver_path = os.getenv('GECKO_DRIVER_PATH')
# driver = Firefox(webdriver.FirefoxProfile(profile), executable_path=driver_path)
LINK_FILE = '../data/game_links.csv'

def sleep(x=1, y=3.5, step=0.5):
    secs = np.random.choice(np.arange(x, y, step))
    time.sleep(secs)

def get_links_data():
    if os.path.isfile(LINK_FILE):
        df = pd.read_csv(LINK_FILE)
    else:
        df = pd.DataFrame(columns=['date', 'link', 'name', 'season'])
    return df

df = get_links_data()
game_dates = set(['20110813', '20120818', '20130817']) # start dates to each season
index = 0
while index < len(game_dates):
    game_date = sorted(list(game_dates))[index]
    mask = df['date'] == game_date
    if mask.sum() > 0:
        print('skipping date {}'.format(game_date))
        index += 1
        continue

    print('fetching link for date {}'.format(game_date))

    api_link = 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?lang=en&region=us&calendartype=whitelist&limit=100&showAirings=true&dates={}&tz=America%2FNew_York&league=eng.1'.format(game_date)
    reponse = requests.get(api_link)
    data = reponse.json()

    # add links
    events = data['events']
    for event in events:
        season = event['season']['year']
        if season > 2013:
            sys.exit('done')

        row = {'date' : game_date,
               'link' : event['links'][0]['href'],
               'name' : event['name'],
               'season' : str(season)}

        df = df.append(row, ignore_index=True)
        print('adding data for {}'.format(event['name']))

    # add dates
    calendar_dates = data['leagues'][0]['calendar']
    calendar_dates = [pd.to_datetime(x).strftime('%Y%m%d') for x in calendar_dates]
    game_dates = game_dates.union(set(calendar_dates))
    index += 1

    sleep(1, 3)

df.to_csv(LINK_FILE, index=False)
