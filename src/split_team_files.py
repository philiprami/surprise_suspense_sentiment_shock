import os
import re
import sys
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = '../data/'
DATASET_DIR = os.path.join(DATA_DIR, 'aggregated')
OUT_DIR = os.path.join(DATASET_DIR, 'team_data')
date_str = datetime.today().strftime('%Y-%m-%d')
os.makedirs(OUT_DIR, exist_ok=True)

prob_cols = ['eff_prob', 'mean_prob', 'median_prob']
emotional_cues = ['surprise' , 'shock']

df = pd.read_csv(os.path.join(DATASET_DIR, f'season_2013_agg_final_{date_str}.csv'))
all_teams = set(df.selection_home.unique()).union(set(df.selection_away.unique()))
out_frames = {}
for team_name in all_teams:
    if not pd.isnull(team_name):
        is_home = df.selection_home == team_name
        is_away = df.selection_away == team_name
        in_play = df.minute.notnull()

        team_df = df[(is_home | is_away) & in_play].reset_index(drop=True)
        team_df.agg_key = pd.to_datetime(team_df.agg_key)
        team_df.sort_values(['Event ID', 'agg_key'], inplace=True)
        team_df['is_home'] = np.where(team_df.selection_home == team_name, 1, 0)
        team_df['fan_tweet'] = np.where(team_df.selection_home == team_name, team_df['fan_tweets_home'], team_df['fan_tweets_away'])
        team_df['fan_retweet_tweet'] = np.where(team_df.selection_home == team_name, (team_df['fan_tweets_home']+team_df['fan_retweets_home']), (team_df['fan_tweets_away']+team_df['fan_retweets_away']))
        team_df['fan_tweet_sent_mean'] = np.where(team_df.selection_home == team_name, team_df['fan_tweet_sent_mean_home'], team_df['fan_tweet_sent_mean_away'])
        team_df['fan_tweet'].fillna(0, inplace=True)
        team_df['fan_retweet_tweet'].fillna(0, inplace=True)
        team_df['fan_tweet_sent_mean'].fillna(0, inplace=True)
        team_df['ln_fan_tweet'] = np.log(team_df['fan_tweet'])
        team_df['ln_fan_retweet_tweet'] = np.log(team_df['fan_retweet_tweet'])
        team_df['ln_fan_tweet_sent_mean'] = np.log(team_df['fan_tweet_sent_mean'])

        team_df['hater_tweet'] = np.where(team_df.selection_home == team_name, team_df['hater_tweets_home'], team_df['hater_tweets_away'])
        team_df['hater_retweet_tweet'] = np.where(team_df.selection_home == team_name, (team_df['hater_tweets_home']+team_df['hater_retweets_home']), (team_df['hater_tweets_away']+team_df['hater_retweets_away']))
        team_df['hater_tweet_sent_mean'] = np.where(team_df.selection_home == team_name, team_df['hater_tweet_sent_mean_home'], team_df['hater_tweet_sent_mean_away'])
        team_df['hater_tweet'].fillna(0, inplace=True)
        team_df['hater_retweet_tweet'].fillna(0, inplace=True)
        team_df['hater_tweet_sent_mean'].fillna(0, inplace=True)
        team_df['ln_hater_tweet'] = np.log(team_df['hater_tweet'])
        team_df['ln_hater_retweet_tweet'] = np.log(team_df['hater_retweet_tweet'])
        team_df['ln_hater_tweet_sent_mean'] = np.log(team_df['hater_tweet_sent_mean'])

        deficit = np.where(team_df.selection_home == team_name, (team_df['home_score']-team_df['away_score']), (team_df['away_score']-team_df['home_score']))
        team_df['multiplier'] = np.where(deficit >= 0 , deficit+1, deficit)
        for cue in emotional_cues:
            for prob in prob_cols:
                team_df[f'own_{cue}_{prob}'] = team_df[f'{cue}_{prob}'] * team_df['multiplier']

        uniq_team_df = pd.DataFrame()
        for i, frame in team_df.groupby('Event ID'):
            last_minute = frame.minute == 45
            end_half = last_minute & frame.event_home.str.contains('end')
            end_index = frame[end_half].iloc[0].name
            drop_index = (frame.index > end_index) & last_minute
            frame = frame[~drop_index]
            for end_i, e in enumerate(frame[last_minute].iterrows()):
                if end_i > 0:
                    index, row = e
                    minute = row['minute'] + float(end_i/10)
                    frame.loc[index, 'minute'] = minute

            extended_play = frame.minute == 91
            for ext_i, e in enumerate(frame[extended_play].iterrows()):
                index, row = e
                minute = row['minute'] + ext_i
                frame.loc[index, 'minute'] = minute

            uniq_team_df = uniq_team_df.append(frame)

        out_frames[team_name] = uniq_team_df

out_frames['C Palace'] = out_frames['C Palace'].append(out_frames['Crystal Palace'])
del out_frames['Crystal Palace']
for team_name, team_df in out_frames.items():
    outfile = os.path.join(OUT_DIR, f'season_2013_agg_final_{date_str}_{team_name}.csv')
    team_df.to_csv(outfile, index=False)
