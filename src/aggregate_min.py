import os
import gc
import sys
import json
import time
import ntpath
import numpy as np
import pandas as pd
from glob import glob
from datetime import timedelta, datetime
import xml.etree.ElementTree as et

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores 11_20/'

with open(DATA_DIR + 'cols.json','r') as column_file:
    cols = json.load(column_file)

with open(DATA_DIR + 'sentiment_map.json', 'r') as json_file:
    file_map = json.load(json_file)
    for x, y in list(file_map.items()):
        file_map[x.replace('_merged', '')] = file_map[x]
    for key in list(file_map.keys()):
        for event_num in file_map[key]:
             file_map[event_num] = file_map[key][event_num]

date_str = datetime.today().strftime('%Y-%m-%d')

team_names = \
{'Crystal Palace': 'C Palace',
 'Manchester City': 'Man City',
 'Manchester United': 'Man Utd',
 'Newcastle United': 'Newcastle',
 'Newcastle':'Newcastle United',
 'Queens Park Rangers': 'QPR',
 'West Bromwich Albion': 'West Brom',
 'Wolverhampton Wanderers': 'Wolves'}

keep_cols = ['Date', 'time', 'Event ID', 'Course', 'Market status', 'selection',
             'selection id', 'agg_key']
new_cols = ['event', 'weighted_sent_mean', 'tweet_sent_mean', 'num_tweets']
agg_results = pd.DataFrame(columns=keep_cols+new_cols)
master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*.csv*'))
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
        all_matches.add(match_id)
        if ((agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)).sum() > 0:
            print('skipping: ', match_id)
            continue

        print(match_id)
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
        game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
        game_start_mask = (match_df['Inplay flag'] == 1) & (match_df['agg_key'] >= game_start)
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
        # I fucked up. Home and away are reversed
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
            if col != 'event':
                merged[col] = merged[col].ffill()
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
        if match_file == 'epl-Crystal Palace-2013-08-18.csv':
            continue

        sent_df = pd.read_csv(SENTIMENT_DIR + match_file)
        sent_df['agg_key'] = sent_df['time'].astype('datetime64[m]')#.astype(str)
        # collect users that use both hashtags
        other_match = next(filter(lambda x: x!= match_file, match_files))
        opp_sent_df = pd.read_csv(SENTIMENT_DIR + other_match)
        obscure_mask = sent_df['tweeter_name'].isin(opp_sent_df['tweeter_name'])
        obscure_names = sent_df[obscure_mask]['tweeter_name'].unique()
        # for obscure users, find how they commented on the first goal
        # if they commented with teams # first, then keep,
        # if they comment with the oppotition # first,  then remove them from the dataset
        # if no goals scored, remove them from the dataset
        game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
        twitter_actual_start = game_start - timedelta(hours=1)
        offset = twitter_actual_start - min(sent_df.agg_key)
        sent_df_ = sent_df.copy()
        sent_df_['time'] = pd.to_datetime(sent_df_['time'])
        opp_sent_df['time'] = pd.to_datetime(opp_sent_df['time'])
        sent_df_.time = sent_df_.time + offset
        opp_sent_df.time = opp_sent_df.time + offset
        sent_df_['time'] = sent_df_['time'].apply(lambda x: x.replace(tzinfo=None))
        opp_sent_df['time'] = opp_sent_df['time'].apply(lambda x: x.replace(tzinfo=None))
        sent_df_.sort_values('time', inplace=True)
        opp_sent_df.sort_values('time', inplace=True)
        comment_df_ = pd.DataFrame([node.attrib for node in xroot])
        comment_df_['last_modified'] = pd.to_datetime(comment_df_['last_modified'])
        for col in ['period', 'minute', 'second']:
            comment_df_[col] = comment_df_[col].astype(float)
        comment_df_.sort_values(['period', 'minute', 'second'], inplace=True)
        goals = (comment_df_.type_id == '16') | (comment_df_.type_id == 16)
        first_goal_time = comment_df_[goals].iloc[0]['last_modified']
        after_goal_mask = (sent_df_['time']>first_goal_time) & sent_df_['tweeter_name'].isin(obscure_names)
        first_comment = sent_df_[after_goal_mask].groupby('tweeter_name')['time'].min()
        first_comment.name = 'team_tweet'
        opp_after_goal_mask = (opp_sent_df['time']>first_goal_time) & opp_sent_df['tweeter_name'].isin(obscure_names)
        first_comment_opp = opp_sent_df[opp_after_goal_mask].groupby('tweeter_name')['time'].min()
        first_comment_opp.name = 'opposition_tweet'
        tweet_times = pd.concat([first_comment, first_comment_opp], axis=1)
        opp_first_mask = (tweet_times['team_tweet'] > tweet_times['opposition_tweet']) | tweet_times['team_tweet'].isnull()
        drop_names = tweet_times[opp_first_mask].index
        drop_mask = sent_df['tweeter_name'].isin(drop_names)

        sent_df = sent_df[~drop_mask].reset_index(drop=True)
        tweet_sent_mean = sent_df.groupby('agg_key')['predictions'].mean()
        tweet_sent_mean.name = 'tweet_sent_mean'
        num_tweets = sent_df.agg_key.value_counts()
        num_tweets.name = 'num_tweets'
        num_retweets = sent_df.groupby('agg_key')['retweets'].sum()
        num_retweets.name = 'num_retweets'
        tweet_df = pd.concat([tweet_sent_mean, num_tweets, num_retweets], axis=1)

        # weighted by retweets
        sent_df.sort_values('agg_key', inplace=True)
        weighted_sent_mean = pd.DataFrame()
        for agg_key in sent_df.agg_key.unique():
            agg_mask = sent_df.agg_key == agg_key
            total_tweets = sent_df[agg_mask].retweets.sum() + agg_mask.sum()
            proportions = (sent_df[agg_mask].retweets + 1) / total_tweets
            weighted = proportions * sent_df[agg_mask].predictions
            weighted_sent_mean = weighted_sent_mean.append({'agg_key' : agg_key,
                                                            'weighted_sent_mean' : weighted.sum()}, ignore_index=True)

        # merge in both tweet cols
        mask = (agg_results['Event ID'] == match_id) & (agg_results['selection'] == selection)
        merged = agg_results[mask].merge(tweet_df.reset_index().rename(columns={'index':'agg_key'}), on='agg_key', how='outer')
        merged = merged.merge(weighted_sent_mean, on='agg_key', how='left')
        if 'weighted_sent_mean_x' in merged.columns:
            merged.drop(columns=['weighted_sent_mean_x', 'tweet_sent_mean_x', 'num_tweets_x', 'num_retweets_x'], inplace=True)
            merged.rename(columns={'weighted_sent_mean_y' : 'weighted_sent_mean',
                                   'tweet_sent_mean_y' : 'tweet_sent_mean',
                                   'num_tweets_y': 'num_tweets',
                                   'num_retweets_y' : 'num_retweets'}, inplace=True)
        merged.sort_values('agg_key', inplace=True)
        for col in merged.columns:
            if col not in ['tweet_sent_mean', 'num_tweets', 'weighted_sent_mean', 'event']:
                merged[col] = merged[col].ffill()

        agg_results = agg_results[~mask].reset_index(drop=True)
        agg_results = agg_results.append(merged)

        # write out progress
        matches_done.add(match_id)
        if len(matches_done) % 50 == 0: # change back to 50
            agg_results.to_csv(OUT_DIR + f'season_2013_agg_event_twitter_{date_str}.csv', index=False)

agg_results.to_csv(OUT_DIR + f'season_2013_agg_event_twitter_{date_str}.csv', index=False)
