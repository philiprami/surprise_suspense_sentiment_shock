'''
Questions:
- Consider merging sentiment scores into one file per game?
- Should retweets be counted? Should they be counted but weighted less?
- Aggregating by millisecond? By second?
- Are we also merging in commentary?
- sentiment and commentary should be merged in at the timestamp exact match or tick directly following
- the more recent sentiment replaces
- if there are multiple matches, puts sentiment in both
- commentary is not by team .. I've gone digging in the text files I scraped to generate the xml commentary contains team-ids..
I would just have to cross-reference this with the website to get the team data
- epl-Crystal Palace-2013-08-18.csv is blank
- neutral commentary counts - and is merged to - for the home team... should they instead be merged to both?
- yellow and red card are the same
- replace match commentary with correct time
- full in sentiment nulls
'''

import os
import json
import ntpath
import pandas as pd
from glob import glob
from collections import defaultdict

DATA_DIR = '/Volumes/My Passport/'
MASTER_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Fracsoft betting data/'
SENTIMENT_DIR = DATA_DIR + 'Suprise, suspense and sentiment from Twitter/Sentiment Scores/'
COMMENTARY_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Match commentaries/'

file_map = defaultdict(lambda: defaultdict(list))

found_files = set()
for csv_file in file_map:
    values = file_map[csv_file].values()
    for sublist in values:
        for item in sublist:
            found_files.add(item)

sentiment_files = glob(SENTIMENT_DIR + '*csv')
sentiment_files = set([ntpath.split(x)[1] for x in sentiment_files])

def get_teams(x):
    split = x.split(' : ')
    match = split[-2]
    away, home = match.split(' v ')
    return pd.Series([away, home])

master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*.csv.gz'))
for master_file in master_files:
    master_dir, master = ntpath.split(master_file)
    df_iter = pd.read_csv(master_file, chunksize=500000, header=None)
    for df in df_iter:
        df_2 = df[[2, 0, 3]].drop_duplicates()
        df_2[['away_team', 'home_team']] = df_2[3].apply(get_teams)
        for i, row in df_2.iterrows():
            if row[2] in file_map[master].keys():
                continue

            sentiment_file_a = 'epl-{}-{}.csv'.format(row['away_team'], row[0])
            sentiment_file_b = 'epl-{}-{}.csv'.format(row['home_team'], row[0])
            if os.path.isfile(SENTIMENT_DIR + sentiment_file_a):
                file_map[master][row[2]].append(sentiment_file_a)
            if os.path.isfile(SENTIMENT_DIR + sentiment_file_b):
                file_map[master][row[2]].append(sentiment_file_b)

file_map = dict(file_map)
for filename in dict(file_map):
    file_map[filename] = dict(file_map[filename])

with open('sentiment_map.json', 'w') as json_file:
    json.dump(file_map, json_file)
