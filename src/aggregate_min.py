import argparse
import os
import gc
import sys
import json
import time
import ntpath
import statistics
import numpy as np
import pandas as pd
from glob import glob
from datetime import timedelta, datetime
import xml.etree.ElementTree as et

CWD = os.path.dirname(__file__)
DATA_DIR = os.path.join(CWD, '..', 'data')
MASTER_DIR = os.path.join(DATA_DIR, 'Fracsoft')
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
COMMENTARY_DIR = os.path.join(DATA_DIR, 'commentaries')
SENTIMENT_DIR = os.path.join(DATA_DIR, 'Sentiment Scores')

def _parse_and_validate_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', '-o',
                        required=True)
    return parser.parse_args()

args = _parse_and_validate_arguments()

with open(os.path.join(DATA_DIR, 'cols.json'),'r') as column_file:
    cols = json.load(column_file)

with open(os.path.join(DATA_DIR, 'sentiment_map.json'), 'r') as json_file:
    file_map = json.load(json_file)
    for x, y in list(file_map.items()):
        file_map[x.replace('_merged', '')] = file_map[x]
    for key in list(file_map.keys()):
        for event_num in file_map[key]:
             file_map[event_num] = file_map[key][event_num]

sent_outliers = pd.read_csv(os.path.join(DATA_DIR, 'sentiment_outliers.csv'))
### original fans
fan_data = pd.read_csv(os.path.join(DATA_DIR, 'favorite_teams.csv'))
hater_data = pd.read_csv(os.path.join(DATA_DIR, 'hater_teams.csv'))

### transformer fans
# fan_data = pd.read_csv(os.path.join(DATA_DIR, 'favorite_teams_transformer.csv'))
# hater_data = pd.read_csv(os.path.join(DATA_DIR, 'hater_teams_transformer.csv'))

### overlap of both models
# fan_data = pd.read_csv(os.path.join(DATA_DIR, 'favorite_teams_overlap.csv'))
# hater_data = pd.read_csv(os.path.join(DATA_DIR, 'hater_teams_overlap.csv'))

team_names = {
    'Crystal Palace': 'C Palace',
    'Manchester City': 'Man City',
    'Manchester United': 'Man Utd',
    'Newcastle United': 'Newcastle',
    'Newcastle':'Newcastle United',
    'Queens Park Rangers': 'QPR',
    'West Bromwich Albion': 'West Brom',
    'Wolverhampton Wanderers': 'Wolves'
}

keep_cols = ['Date', 'time', 'Event ID', 'Course', 'Market status', 'selection',
             'selection id', 'agg_key']
new_cols = ['event', 'tweet_sent_mean', 'num_tweets', 'num_retweets',
            'fan_tweets', 'fan_retweets', 'fan_tweet_sent_mean',
            'hater_tweets', 'hater_retweets', 'hater_tweet_sent_mean']

agg_results = pd.DataFrame(columns=keep_cols+new_cols)
master_files = sorted(glob(os.path.join(MASTER_DIR, '*season_2013_match_part*.csv*')))
matches_done = set()
all_matches = set()
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
        # sys.exit()
        all_matches.add(match_id)
        if ((agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)).sum() > 0:
            print('skipping: ', match_id)
            continue

        courses = match_df.Course.unique()
        if len(courses) > 1:
            course = next(filter(lambda x: 'Second Half Match Odds' not in x, courses))
            match_df['Course'] = course

        print(match_df['Course'].unique())
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
            # agg_results = pd.concat([agg_results, results], ignore_index=True)

        # merge in event
        match_df.sort_values('datetime', inplace=True)
        game_start = pd.to_datetime(f'{statistics.mode(match_df.Date)} {statistics.mode(match_df.time)}')
        game_start_mask = (match_df['Inplay flag'] == 1) & (match_df['agg_key'] >= game_start)
        if game_start_mask.sum() < 1:
            continue

        actual_start = match_df[game_start_mask].sort_values('datetime').iloc[0]['datetime']
        game_end = match_df[match_df['Inplay flag'] == 1].sort_values('datetime').iloc[-1]['datetime']
        xml_name = ';'.join(match_df['Course'].iloc[0].split(':')[:-1]).strip() + '.xml'
        xml_file = os.path.join(COMMENTARY_DIR, master.replace('.csv.gz', '/').replace('.csv', '/'), xml_name)
        if not os.path.isfile(xml_file):
            print('missing ', xml_name)
            continue

        xtree = et.parse(xml_file)
        xroot = xtree.getroot()
        comment_df = pd.DataFrame([node.attrib for node in xroot])
        # I messed up. Home and away are reversed
        reverse_dict = {xroot.attrib['home_team_name'].replace('2', '') : xroot.attrib['away_team_name'].replace('2', ''),
                        xroot.attrib['away_team_name'].replace('2', '') : xroot.attrib['home_team_name'].replace('2', ''),
                        'The Draw' : 'The Draw'}
        card_mask = comment_df['type_id'] == '17'
        red_cards = card_mask & comment_df['comment'].str.contains('red', case=False)
        yellow_cards = card_mask & comment_df['comment'].str.contains('yellow', case=False)
        comment_df.loc[yellow_cards, 'type'] = 'yellow card'
        comment_df.loc[yellow_cards, 'type_id'] = '20'
        comment_df.loc[red_cards, 'type'] = 'red card'
        comment_df.loc[red_cards, 'type_id'] = '21'
        goal_mask = comment_df['type_id'] == '16'
        own_goal = goal_mask & comment_df['comment'].str.contains('own goal', case=False)
        comment_df.loc[own_goal, 'type'] = 'own goal'
        comment_df.second = comment_df.second.fillna(0)
        second_half_index = comment_df[comment_df['comment'] == 'Second half begins!'].iloc[0].name
        second_half = comment_df[comment_df.index <= second_half_index]
        second_half.iloc[0]['last_modified'] = game_end
        game_end_seconds = int(second_half.iloc[0]['second']) + int(second_half.iloc[0]['minute']) * 60
        second_half['last_modified'] = second_half[['minute', 'second']].\
          apply(lambda x: game_end - timedelta(seconds=(game_end_seconds - (int(x[1]) + int(x[0]) * 60))), axis=1)
        first_half = comment_df[comment_df.index > second_half_index]
        first_half['last_modified'] = first_half[['minute', 'second']].\
          apply(lambda x: actual_start + timedelta(minutes=int(x[0]), seconds=int(x[1])), axis=1)
        comment_df = pd.concat([second_half, first_half])
        comment_df['team'] = comment_df['team'].str.replace('2', '')
        try:
            comment_df = comment_df[comment_df['team'] == reverse_dict[selection]]
        except KeyError:
            comment_df = comment_df[comment_df['team'] == reverse_dict[team_names[selection]]]
        comment_df['agg_key'] = comment_df['last_modified'].astype('datetime64[m]')
        event_ag = comment_df.sort_values('last_modified').groupby('agg_key')['type'].unique()
        mask = (agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)
        merged = event_ag.reset_index().merge(agg_results[mask], on='agg_key', how='outer')
        merged.sort_values('agg_key', inplace=True)
        merged.loc[merged.type.notnull(), 'type'] = merged[merged.type.notnull()]['type'].apply(lambda x: ','.join(x))
        if 'event' in merged.columns:
            merged.drop(columns=['event'], inplace=True)
        merged.rename(columns={'type' : 'event'}, inplace=True)
        for col in merged.columns:
            if col != 'event' and 'tweet' not in col:
                merged[col] = merged[col].bfill()

        agg_results = agg_results[~mask]
        agg_results = agg_results.append(merged, ignore_index=True)

        # merge in twitter numbers
        if str(match_id) not in file_map:
            print('missing match twitter data: ', match_df.iloc[0]['Course'])
            continue

        match_files = file_map[str(match_id)]
        selection_files = [x for x in match_files if selection in x]
        if selection == 'The Draw':
            continue

        if len(selection_files) != 1:
            print('missing selection: ', selection)
            print(match_files)
            continue

        match_file = selection_files[0]
        if 'epl-Crystal Palace-2013-08-18.csv' in match_file:
            continue

        sent_df = pd.read_csv(os.path.join(SENTIMENT_DIR, match_file))
        ### remove outliers
        sent_df = sent_df.join(sent_outliers[sent_outliers['file_name'] == match_file].reset_index()['outlier'])
        sent_df = sent_df[sent_df['outlier'] == 0].reset_index(drop=True)
        ###################
        sent_df['agg_key'] = sent_df['time'].astype('datetime64[m]') #.astype(str)
        tweet_sent_mean = sent_df.groupby('agg_key')['predictions'].mean()
        # tweet_sent_mean = sent_df.groupby('agg_key')['score'].mean()
        tweet_sent_mean.name = 'tweet_sent_mean'
        num_tweets = sent_df.agg_key.value_counts()
        num_tweets.name = 'num_tweets'
        num_retweets = sent_df.groupby('agg_key')['retweets'].sum()
        num_retweets.name = 'num_retweets'

        other_file = next(filter(lambda x: selection not in x, match_files))
        other_sent_df = pd.read_csv(os.path.join(SENTIMENT_DIR, other_file))
        ### remove outliers
        other_sent_df = other_sent_df.join(sent_outliers[sent_outliers['file_name'] == other_file].reset_index()['outlier'])
        other_sent_df = other_sent_df[other_sent_df['outlier'] == 0].reset_index(drop=True)
        ###################
        other_sent_df['agg_key'] = other_sent_df['time'].astype('datetime64[m]') #.astype(str)
        other_fan_df = other_sent_df.merge(fan_data, left_on='tweeter_name', right_on='twitter_name', how='left')
        other_fan_mask = other_fan_df['fav_team'] == selection
        other_fan_tweets = other_fan_df[other_fan_mask].agg_key.value_counts()
        other_fan_retweets = other_fan_df[other_fan_mask].groupby('agg_key')['retweets'].sum()

        fan_df = sent_df.merge(fan_data, left_on='tweeter_name', right_on='twitter_name', how='left')
        fan_mask = fan_df['fav_team'] == selection
        # fan_tweets = fan_df[fan_mask].agg_key.value_counts() + other_fan_tweets
        fan_tweets = pd.concat([fan_df[fan_mask].agg_key.value_counts(), other_fan_tweets], axis=1).sum(axis=1)
        fan_tweets.name = 'fan_tweets'
        # fan_retweets = fan_df[fan_mask].groupby('agg_key')['retweets'].sum() + other_fan_retweets
        fan_retweets = pd.concat([fan_df[fan_mask].groupby('agg_key')['retweets'].sum(), other_fan_retweets], axis=1).sum(axis=1)
        fan_retweets.name = 'fan_retweets'
        fan_tweet_sent_mean = fan_df[fan_mask].groupby('agg_key')['predictions'].mean()
        # fan_tweet_sent_mean = fan_df[fan_mask].groupby('agg_key')['score'].mean()
        fan_tweet_sent_mean.name = 'fan_tweet_sent_mean'

        hater_df = sent_df.merge(hater_data, left_on='tweeter_name', right_on='twitter_name', how='left')
        hater_mask = hater_df['hater_team'] == selection
        hater_tweets = hater_df[hater_mask].agg_key.value_counts()
        hater_tweets.name = 'hater_tweets'
        hater_retweets = hater_df[hater_mask].groupby('agg_key')['retweets'].sum()
        hater_retweets.name = 'hater_retweets'
        hater_tweet_sent_mean = hater_df[hater_mask].groupby('agg_key')['predictions'].mean()
        # hater_tweet_sent_mean = hater_df[hater_mask].groupby('agg_key')['score'].mean()
        hater_tweet_sent_mean.name = 'hater_tweet_sent_mean'

        tweet_df = pd.concat([tweet_sent_mean, num_tweets, num_retweets,
                              fan_tweets, fan_retweets, fan_tweet_sent_mean,
                              hater_tweets, hater_retweets, hater_tweet_sent_mean], axis=1)

        # merge in both tweet cols
        mask = (agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)
        merged = agg_results[mask].merge(tweet_df.reset_index().rename(columns={'index':'agg_key'}), on='agg_key', how='outer')
        if 'tweet_sent_mean_x' in merged.columns:
            merged.drop(columns=['tweet_sent_mean_x', 'num_tweets_x', 'num_retweets_x',
                                 'fan_tweets_x', 'fan_retweets_x', 'fan_tweet_sent_mean_x',
                                 'hater_tweets_x', 'hater_retweets_x', 'hater_tweet_sent_mean_x'], inplace=True)
            merged.rename(columns={'tweet_sent_mean_y' : 'tweet_sent_mean',
                                   'num_tweets_y': 'num_tweets',
                                   'num_retweets_y' : 'num_retweets',
                                   'fan_tweets_y' : 'fan_tweets',
                                   'fan_retweets_y' : 'fan_retweets',
                                   'fan_tweet_sent_mean_y' : 'fan_tweet_sent_mean',
                                   'hater_tweets_y' : 'hater_tweets',
                                   'hater_retweets_y' : 'hater_retweets',
                                   'hater_tweet_sent_mean_y' : 'hater_tweet_sent_mean'},
                                   inplace=True)
        merged.sort_values('agg_key', inplace=True)
        for col in merged.columns:
            if col not in ['tweet_sent_mean', 'num_tweets', 'num_retweets', 'event',
                           'fan_tweets', 'fan_retweets', 'fan_tweet_sent_mean',
                           'hater_tweets', 'hater_retweets', 'hater_tweet_sent_mean']:
                merged[col] = merged[col].bfill()

        agg_results = agg_results[~mask].reset_index(drop=True)
        agg_results = agg_results.append(merged)

        # write out progress
        matches_done.add(match_id)
        # if len(matches_done) % 50 == 0:
        if len(matches_done) == 2:
            agg_results.to_csv(args.output, index=False)
            sys.exit()

agg_results.to_csv(args.output, index=False)
