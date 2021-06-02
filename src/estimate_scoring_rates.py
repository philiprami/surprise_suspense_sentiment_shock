'''
Step 1 of calculating suspense
'''

import os
import gc
import sys
import json
import time
import ntpath
import numpy as np
import pandas as pd
from glob import glob
from datetime import timedelta
from collections import defaultdict
import xml.etree.ElementTree as et

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'

with open(DATA_DIR + 'cols.json','r') as column_file:
    cols = json.load(column_file)

scoring_rates = defaultdict(dict)
master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*.csv*'))
for master_file in master_files:
    master_dir, master = ntpath.split(master_file)
    df = pd.read_csv(master_file, header=None)
    df.columns = [str(x) for x in df.columns]
    df.rename(columns=cols, inplace=True)
    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'] + 'T' + df['Time stamp']).dt.round('s')
    else:
        df['datetime'] = pd.to_datetime(df['datetime'])

    df = df[df['selection'] != 'Draw'].reset_index(drop=True)
    gb = df.groupby('Event ID')
    for match_id, match_df in gb:
        if match_id in scoring_rates:
            continue

        match_df.sort_values('datetime', inplace=True)
        game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
        game_start_mask = (match_df['Inplay flag'] == 1) & (match_df['datetime'] >= game_start)
        if game_start_mask.sum() < 1:
            continue

        team_mask = ~match_df['selection'].str.contains('/')
        teams = list(filter(lambda x: x != 'The Draw', match_df[team_mask]['selection'].unique()))
        actual_start_index = match_df[game_start_mask].sort_values('datetime').iloc[0]['datetime']
        pre_match = match_df.datetime < actual_start_index
        closing_odds = {}
        for selection, selection_df in match_df[pre_match].groupby('selection'):
            selection_df.sort_values('datetime', inplace=True)
            closing_row = selection_df.iloc[-1]
            closing_odds[selection] = 1/closing_row['last price matched']
            team_mask = ~match_df['selection'].str.contains('/')
            match_df[team_mask]['selection'].unique()

        # minimize scoring rate
        def min_scoring_rate(num_goals, market_odds, lmbda):
            poi_dis = poisson(lmbda)
            prediciton = 1 - poi_dis.cdf(num_goals)
            diff = prediciton - market_odds
            return diff*diff

        for team in teams:
            key = f'{team}/Over 2.5 Goals'
            if key not in closing_odds:
                print(f'no over odds for team {team}. match {match_id}')
                continue
                
            over_prob = closing_odds[key]
            objective = {}
            for lmbda in np.arange(0, 20, 0.01):
                diff = min_scoring_rate(3, over_prob, lmbda)
                objective[lmbda] = diff

            scoring_rate = sorted(objective.items(), key=lambda x: x[1])[0][0]
            scoring_rates[match_id][team] = scoring_rate

# write scoring rates to json
with open(os.path.join(DATA_DIR, 'scoring_rates.json'), 'w') as json_file:
    json.dump(scoring_rates, json_file)
