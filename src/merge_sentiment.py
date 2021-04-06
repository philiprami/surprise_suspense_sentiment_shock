import os
import gc
import sys
import json
import time
import ntpath
import numpy as np
import pandas as pd
from glob import glob
import xml.etree.ElementTree as et

DATA_DIR = '/Volumes/My Passport/'
MASTER_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Fracsoft betting data/'
SENTIMENT_DIR = DATA_DIR + 'Suprise, suspense and sentiment from Twitter/Sentiment Scores/'
DATA_DIR = 'data/'
MASTER_DIR = DATA_DIR + 'merged/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'

with open('sentiment_map.json', 'r') as json_file:
    file_map = json.load(json_file)

with open('missing_sentiment.txt', 'r') as txt_file:
    missing_sentiment = set()
    for line in txt_file:
        missing_sentiment.add(line.strip())

with open('cols.json','r') as column_file:
    cols = json.load(column_file)

master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*_merged.csv'))
for master_file in master_files:
    master_dir, master = ntpath.split(master_file)
    df = pd.read_csv(master_file)
    df.rename(columns=cols, inplace=True)
    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['0'] + 'T' +df['6']).dt.round('s')
    else:
        df['datetime'] = pd.to_datetime(df['datetime'])

    # add cols to be
    if 'sent_mean' not in df.columns:
        df['sent_mean'] = None
    if 'sent_med' not in df.columns:
        df['sent_med'] = None
    if 'num_tweets' not in df.columns:
        df['num_tweets'] = None
    if 'num_retweets' not in df.columns:
        df['num_retweets'] = None

    gb = df.groupby('Event ID')
    for match_id, match_df in gb:
        for x, y in list(file_map.items()):
            file_map[x.replace('.gz', '')] = file_map[x]

        if str(match_id) not in file_map[master]:
            missing_sentiment.add(str(match_id))
            continue

        match_files = file_map[master][str(match_id)]
        for match_file in match_files:
            # check if file already processed
            if match_file == 'epl-Crystal Palace-2013-08-18.csv':
                print('skipping: ' + match_file)
                continue

            print('reading match file: ' + match_file)
            sent_df = pd.read_csv(SENTIMENT_DIR + match_file)
            sent_df['datetime'] = sent_df['time'].astype('datetime64[m]') # change to s to agg by second
            sent_df.sort_values('datetime', inplace=True)
            sent_df['time_key'] = np.where(sent_df['datetime'].isin(match_df['datetime'].astype('datetime64[m]')), \
              sent_df['datetime'], None)
            if sent_df['time_key'].dtype == 'O': # np.where changes dtype of datetime for some reason
                sent_df['time_key'] = sent_df['time_key'].astype('datetime64[m]')

            sent_df['time_key'] = sent_df['time_key'].bfill()
            team_name = match_file.split('-')[1]
            team_mask = match_df['10'] == team_name
            max_time = match_df[team_mask]['datetime'].max()
            for i, row in sent_df[sent_df['time_key'].isnull()].iterrows(): # fill in null values
                if row['datetime'] > max_time:
                    sent_df.loc[i, 'time_key'] = max_time
                    continue

                time_diff = match_df[team_mask]['datetime'] - row['datetime']
                sent_df.loc[i, 'time_key'] = match_df[team_mask][time_diff > pd.Timedelta(0)].iloc[0]['datetime']

            # aggregate
            ag_sent = sent_df.groupby('time_key')['sentiment'].mean() # use mean for now
            ag_sent.name = 'sent_mean'
            med_sent = sent_df.groupby('time_key')['sentiment'].median()
            med_sent.name = 'sent_med'


            merged = match_df[team_mask].merge(ag_sent, how='left', left_on='datetime',
                                               right_on='time_key', suffixes=('_y', ''))
            merged = merged.merge(med_sent, how='left', left_on='datetime', right_on='time_key',
                                  suffixes=('_y', ''))
            merged = merged[[col for col in df.columns if '_y' not in col]]

            # replace rows in master df with newly merged sentiment df
            replace_mask = (df['2'] == match_id) & (df['10'] == team_name)
            merged.set_index(df[replace_mask].index, inplace=True)
            df.loc[replace_mask] = merged

            # delete vars to save memory
            merged_files.add(match_file)
            del sent_df
            del ag_sent

        del match_df
        gc.collect()

    df.to_csv(master_file, index=False)

with open('merged_files.txt', 'w') as txt_file:
    for filename in merged_files:
        txt_file.write(filename + '\n')

with open('missing_sentiment.txt', 'w') as txt_file:
    for mkey in missing_sentiment:
        txt_file.write(mkey + '\n')
