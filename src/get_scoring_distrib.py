'''
Step 2 of calculating suspense
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
import xml.etree.ElementTree as et

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'

with open(DATA_DIR + 'cols.json','r') as column_file:
    cols = json.load(column_file)

minute_goals = Counter()
num_matches = 0
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

    df = df[~df['selection'].str.contains('Over |Under ')].reset_index(drop=True)
    df = df[~df['selection'].str.contains('/', regex=False)].reset_index(drop=True)
    df = df[df['selection'] != 'Draw'].reset_index(drop=True)
    gb = df.groupby('Event ID')
    for match_id, match_df in gb:
        print(match_id)
        match_df.sort_values('datetime', inplace=True)
        match_df['agg_key'] = match_df['datetime'].astype('datetime64[m]')
        game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
        game_start_mask = (match_df['Inplay flag'] == 1) & (match_df['datetime'] >= game_start)
        if game_start_mask.sum() < 1:
            continue

        actual_start = match_df[game_start_mask].sort_values('datetime').iloc[0]['datetime']
        game_end = match_df[match_df['Inplay flag'] == 1].sort_values('datetime').iloc[-1]['datetime']
        xml_name = ';'.join(match_df['Course'].iloc[0].split(':')[:-1]).strip() + '.xml'
        xml_file = COMMENTARY_DIR + master.replace('.csv.gz', '/').replace('.csv', '/') + xml_name
        if not os.path.isfile(xml_file):
            print('missing ', xml_name)
            continue

        xtree = et.parse(xml_file)
        xroot = xtree.getroot()
        comment_df = pd.DataFrame([node.attrib for node in xroot])
        comment_df.second = comment_df.second.fillna(0)
        comment_df.minute = comment_df.minute.astype(int)
        second_half_index = comment_df[comment_df['comment'] == 'Second half begins!'].iloc[0].name
        second_half = comment_df[comment_df.index <= second_half_index]
        second_half.iloc[0]['last_modified'] = game_end
        game_end_seconds = int(second_half.iloc[0]['second']) + int(second_half.iloc[0]['minute']) * 60
        second_half['last_modified'] = second_half[['minute', 'second']].\
          apply(lambda x: game_end - timedelta(seconds=(game_end_seconds - (int(x[1]) + int(x[0]) * 60))), axis=1)
        first_half = comment_df[comment_df.index > second_half_index]
        first_half['last_modified'] = first_half[['minute', 'second']].\
          apply(lambda x: actual_start + timedelta(minutes=int(x[0]), seconds=int(x[1])), axis=1)
        second_half.loc[second_half['minute'] > 90, 'minute'] = 90
        first_half.loc[first_half['minute'] > 45, 'minute'] = 45
        comment_df = pd.concat([second_half, first_half])
        comment_df['goal_scored'] = np.where(comment_df.type == 'goal scored', 1, 0)
        minute_goals += Counter(comment_df.groupby('minute')['goal_scored'].sum().to_dict())

# moving average over 93 minutes
distribution = {}
min_goals_df = pd.DataFrame(minute_goals, index=['goals']).T
min_goals_df.sort_index(inplace=True)
for i in range(94):
    if i < 14:
        distribution[i] = np.nan
        continue

    if i not in min_goals_df.index:
        min_goals_df = min_goals_df.append({'goals' : 0}, ignore_index=True)

    i_minus_1 = i - 15
    slice_df = min_goals_df.loc[i_minus_1+1:i]
    distribution[i] = slice_df['goals'].mean()

# density, write to file
distrb_intpltd = pd.DataFrame(distribution, index=[0]).T[0].interpolate(limit_direction='backward').to_frame(name='goals')
distrb_intpltd['density'] = distrb_intpltd['goals'] / distrb_intpltd['goals'].sum()
distrb_intpltd.to_csv(DATA_DIR + 'scoring_distribution.csv')

with open(DATA_DIR + 'cols.csv','r') as column_file:
    cols = json.load(column_file)

distrb_intpltd['expctd_goals'] = distrb_intpltd['density'] * scoring_rate
