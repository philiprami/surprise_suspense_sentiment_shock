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

with open(DATA_DIR + 'sentiment_map.json', 'r') as json_file:
    file_map = json.load(json_file)
    for x, y in list(file_map.items()):
        file_map[x.replace('_merged', '')] = file_map[x]
    for key in list(file_map.keys()):
        for event_num in file_map[key]:
             file_map[event_num] = file_map[key][event_num]

keep_cols = ['Date', 'time', 'Event ID', 'Course', 'Market status', 'selection',
             'selection id', 'agg_key']
new_cols = ['event', 'weighted_sent_mean', 'tweet_sent_mean']
agg_results = pd.DataFrame(columns=keep_cols+new_cols)
master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*.csv*'))
matches_done = set()
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
    gb = df.groupby(['Event ID', 'selection'])
    for (match_id, selection), match_df in gb:
        matches_done.add(match_id)
        print(match_id)
        if ((agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)).sum() > 0:
            print('skipping: ', match_id)
            continue

        match_df.sort_values('datetime', inplace=True)
        match_df['agg_key'] = match_df['datetime'].astype('datetime64[m]')
        min_gb = match_df.groupby('agg_key')
        for agg_key, min_df in min_gb:
            min_df['eff_price_match'] = min_df['total matched'] * min_df['last price matched']
            eff_price_match = (min_df['eff_price_match'] / min_df['total matched'].sum()).sum()
            min_df = min_df[(min_df['total matched'] > 0) & (min_df['Market status'] == 'Active')]
            mean_price_match = min_df['last price matched'].mean()
            median_price_match = min_df['last price matched'].median()
            results = min_df[keep_cols].drop_duplicates()
            if results.shape[0] > 1:
                course = min_df['Course'].mode()[0]
                min_df['Course'] = course
                results = min_df[keep_cols].drop_duplicates()
                if results.shape[0] > 1:
                    sys.exit('too many results')

            results['Inplay flag'] = 1 if 1 in min_df['Inplay flag'].unique() else 0
            results['eff_price_match'] = eff_price_match
            results['mean_price_match'] = mean_price_match
            results['median_price_match'] = median_price_match
            agg_results = agg_results.append(results, ignore_index=True)

        # merge in event
        match_df.sort_values('datetime', inplace=True)
        game_start = match_df[match_df['Inplay flag'] == 1].sort_values('datetime').iloc[0]['datetime']
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
        second_half_index = comment_df[comment_df['comment'] == 'Second half begins!'].iloc[0].name
        second_half = comment_df[comment_df.index <= second_half_index]
        second_half.iloc[0]['last_modified'] = game_end
        game_end_seconds = int(second_half.iloc[0]['second']) + int(second_half.iloc[0]['minute']) * 60
        second_half['last_modified'] = second_half[['minute', 'second']].\
          apply(lambda x: game_end - timedelta(seconds=(game_end_seconds - (int(x[1]) + int(x[0]) * 60))), axis=1)
        first_half = comment_df[comment_df.index > second_half_index]
        first_half['last_modified'] = first_half[['minute', 'second']].\
          apply(lambda x: game_start + timedelta(minutes=int(x[0]), seconds=int(x[1])), axis=1)
        comment_df = pd.concat([second_half, first_half])
        comment_df = comment_df[comment_df['team'] == selection]
        comment_df['agg_key'] = comment_df['last_modified'].astype('datetime64[m]')
        event_ag = comment_df.sort_values('last_modified').groupby('agg_key')['type'].unique()
        mask = (agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)
        merged = agg_results[mask].merge(event_ag, on='agg_key', how='left')
        merged.loc[merged.type.notnull(), 'type'] = merged[merged.type.notnull()]['type'].apply(lambda x: ','.join(x))
        if 'event' in merged.columns:
            merged.drop(columns=['event'], inplace=True)
        merged.rename(columns={'type' : 'event'}, inplace=True)
        merged.set_index(agg_results[mask].index, inplace=True)
        agg_results.loc[mask] = merged

        # merge in twitter numbers
        # if ((agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection) & agg_results['tweets'].notnull()).sum() > 0:
        #     print('skipping: ', match_id)
        #     continue

    #################### DELETE THIS
    # done = set()
    # agg_results = pd.read_csv(OUT_DIR + 'season_2013_agg_minute_metrics.csv')
    # # agg_results['tweet_sent_mean'] = None
    # # agg_results['weighted_sent_mean'] = None
    # gb = agg_results.groupby(['Event ID', 'selection'])
    # for (match_id, selection), match_df in gb:
    #     print(match_id)
    #     if ((agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection) & agg_results['tweet_sent_mean'].notnull()).sum() > 0:
    #         print('skipping: ', match_id)
    #         continue
    ####################

        if str(match_id) not in file_map:#[master]:
            print('missing match twitter data: ', match_df.iloc[0]['Course'])
            continue

        # match_files = file_map[master][str(match_id)]
        match_files = file_map[str(match_id)]
        selection_files = [x for x in match_files if selection in x]
        if selection == 'The Draw':
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
        tweet_sent_mean = sent_df.groupby('agg_key')['predictions'].mean()
        tweet_sent_mean.name = 'tweet_sent_mean'

        # weighted by retweets
        weighted_sent_mean = pd.DataFrame()
        for agg_key in sent_df.agg_key.unique():
            agg_mask = sent_df.agg_key == agg_key
            total_tweets = sent_df[agg_mask].retweets.sum() + agg_mask.sum()
            proportions = (sent_df[agg_mask].retweets + 1) / total_tweets
            weighted = proportions * sent_df[agg_mask].predictions
            weighted_sent_mean = weighted_sent_mean.append({'agg_key' : agg_key, 'weighted_sent_mean' : weighted.sum()}, ignore_index=True)

        # merge in both tweet cols
        mask = (agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)
        merged = agg_results[mask].merge(tweet_sent_mean, on='agg_key', how='left')
        merged = merged.merge(weighted_sent_mean, on='agg_key', how='left')
        if 'weighted_sent_mean_x' in merged.columns:
            merged.drop(columns=['weighted_sent_mean_x', 'tweet_sent_mean_x'], inplace=True)
            merged.rename(columns={'weighted_sent_mean_y' : 'weighted_sent_mean', 'tweet_sent_mean_y' : 'tweet_sent_mean'}, inplace=True)
        merged.set_index(agg_results[mask].index, inplace=True)
        agg_results.loc[mask] = merged
        # done.add(f'{match_id}-{selection}')

        # write out progress
        if len(matches_done) % 50 == 0:
            agg_results.to_csv(OUT_DIR + 'season_2013_agg_event_twitter_3103.csv', index=False)

agg_results.to_csv(OUT_DIR + 'season_2013_agg_event_twitter_3103.csv', index=False)

# CHECKS
# 3 selections
# tweets and rewtweets for both teams in each match
# events for both teams of each match
