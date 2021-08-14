import os
import sys
import json
import numpy as np
import pandas as pd

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'

with open(DATA_DIR + 'sentiment_map.json', 'r') as json_file:
    file_map = json.load(json_file)
    for x, y in list(file_map.items()):
        file_map[x.replace('_merged', '')] = file_map[x]
    for key in list(file_map.keys()):
        for event_num in file_map[key]:
             file_map[event_num] = file_map[key][event_num]

INPUT = pd.read_csv(OUT_DIR + 'season_2013_agg_event_twitter_0810.csv')
OUTPUT = pd.DataFrame()

gb = INPUT.groupby(['Event ID', 'selection'])
for (match_id, selection), match_df in gb:
    # merge in twitter numbers
    if str(match_id) not in file_map:
        print('missing match twitter data: ', match_df.iloc[0]['Course'])
        continue

    match_files = file_map[str(match_id)]
    selection_files = [x for x in match_files if selection in x]
    if selection == 'The Draw':
        OUTPUT = OUTPUT.append(match_df.set_index('agg_key'))
        continue

    if len(selection_files) != 1:
        print('missing selection: ', selection)
        print(match_files)
        continue

    match_file = selection_files[0]
    if match_file == 'epl-Crystal Palace-2013-08-18.csv':
        continue

    sent_df = pd.read_csv(SENTIMENT_DIR + match_file)
    sent_df['agg_key'] = sent_df['time'].astype('datetime64[m]')#.astype(str)
    match_df['agg_key'] = match_df['agg_key'].astype('datetime64[m]')
    num_tweets = sent_df.agg_key.value_counts()
    num_tweets.name = 'num_tweets'
    merged = match_df.set_index('agg_key').join(num_tweets, how='left')
    OUTPUT = OUTPUT.append(merged)

OUTPUT.reset_index().to_csv(OUT_DIR + 'season_2013_agg_event_twitter_0810_copy.csv', index=False)
