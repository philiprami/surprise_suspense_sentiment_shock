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

DATA_DIR = '/Volumes/My Passport/'
MASTER_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Fracsoft betting data/'
COMMENTARY_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Match commentaries/'
COMMENTARY_HIERARCHY = ['13', '18', '19', '10', '15', '10000', '6', '16','30', '32']

dtypes_dict = {6 : 'corner',
               10 : 'save',
               13 : 'missed',
               14 : 'woodwork',
               15 : 'blocked',
               16 : 'goal',
               17 : 'card',
               18 : 'substitution',
               19 : 'substitution',
               30 : 'end',
               32 :'start',
               10000 : 'offside'}

with open('sentiment_map.json', 'r') as json_file:
    file_map = json.load(json_file)

with open('merged_files.txt', 'r') as txt_file:
    merged_files = set()
    for line in txt_file:
        merged_files.add(line.strip())

with open('missing_commentary.txt', 'r') as txt_file:
    missing_commentary = set()
    for line in txt_file:
        missing_commentary.add(line.strip())

master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*_merged.csv.gz'))
for master_file in master_files:
    master_dir, master = ntpath.split(master_file)
    df = pd.read_csv(master_file)
    df.columns = [str(x) for x in df.columns]
    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['0'] + 'T' +df['6']).dt.round('s')
    else:
        df['datetime'] = pd.to_datetime(df['datetime'])
    if 'event' not in df.columns:
        df['event'] = None

    gb = df.groupby('2')
    for match_id, match_df in gb:
        match_df.sort_values('datetime', inplace=True)
        game_start = match_df[match_df['7'] == 1].iloc[0]['datetime']
        xml_name = ';'.join(match_df['3'].iloc[0].split(':')[:-1]).strip() + '.xml'
        xml_file = COMMENTARY_DIR + master.replace('_merged.csv.gz', '/') + xml_name
        if not os.path.isfile(xml_file):
            missing_commentary.add(xml_name)
            continue
        if xml_name in merged_files or xml_name == 'Soccer ; English Soccer ; Barclays Premier League ; Fixtures 18 August ; Crystal Palace v Tottenham.xml':
            print('skipping: ' + xml_name)
            continue

        print('reading match file: ' + xml_name)
        xtree = et.parse(xml_file)
        xroot = xtree.getroot()
        comment_df = pd.DataFrame([node.attrib for node in xroot])
        comment_df.second = comment_df.second.fillna(0)
        comment_df['last_modified'] = \
          comment_df[['minute', 'second']].apply(lambda x: game_start + timedelta(minutes=int(x[0]), seconds=int(x[1])),
                                                 axis=1)

        # comment_df['last_modified'] = pd.to_datetime(comment_df['last_modified'])
        comment_df['type'] = comment_df['type_id'].apply(lambda x: dtypes_dict[int(x)])
        for team_name, comm_df in comment_df.groupby('team'):
            comm_df.sort_values('last_modified', inplace=True)
            team_mask = match_df['10'] == team_name
            comm_df['time_key'] = \
              np.where(comm_df['last_modified'].isin(match_df[team_mask]['datetime']), comm_df['last_modified'], None)
            if comm_df['time_key'].dtype == 'O': # np.where changes dtype of datetime for some reason
                comm_df['time_key'] = comm_df['time_key'].astype('datetime64[s]')

            comm_df['time_key'] = comm_df['time_key'].bfill()
            for i, row in comm_df[comm_df['time_key'].isnull()].iterrows(): # fill in null values at the end
                time_diff = match_df[team_mask]['datetime'] - row['last_modified']
                comm_df.loc[i, 'time_key'] = match_df[team_mask][time_diff > pd.Timedelta(0)].iloc[0]['datetime']

            ag_df = comm_df.groupby('time_key')['type'].unique()
            ag_sorted = ag_df.apply(lambda x: ' '.join(sorted(x)))
            ag_sorted.name = 'event'
            if 'event' in match_df.columns: # avoid duplication of sentiment column
                del match_df['event']

            merged = match_df[team_mask].merge(ag_sorted, how='left', left_on='datetime', right_on='time_key')

            # replace rows in master df with newly merged sentiment df
            replace_mask = (df['2'] == match_id) & (df['10'] == team_name)
            merged.set_index(df[replace_mask].index, inplace=True)
            df.loc[replace_mask] = merged

        # delete vars to save memory
        merged_files.add(xml_name)
        del comment_df
        del comm_df
        del merged
        del match_df
        gc.collect()

    df.to_csv(master_file, index=False)

with open('merged_files.txt', 'w') as txt_file:
    for filename in sorted(merged_files):
        txt_file.write(filename + '\n')

with open('missing_commentary.txt', 'w') as txt_file:
    for mkey in missing_commentary:
        txt_file.write(mkey + '\n')
