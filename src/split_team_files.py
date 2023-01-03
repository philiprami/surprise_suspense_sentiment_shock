import os
import re
import sys
import argparse
import numpy as np
import pandas as pd
from datetime import datetime

emotional_cues = ['surprise', 'shock']

def _parse_and_validate_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i',
                        required=True)
    parser.add_argument('--output', '-o',
                        required=True)
    return parser.parse_args()

args = _parse_and_validate_arguments()
os.makedirs(args.output, exist_ok=True)
df = pd.read_csv(args.input)
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
        home_cols = [x for x in team_df.columns if 'home' in x]
        away_cols = [x for x in team_df.columns if 'away' in x]
        for home_col, away_col in zip(home_cols, away_cols):
            col = home_col.replace('_home', '').replace('home_', '')
            team_df[col] = np.where(team_df.selection_home == team_name, team_df[home_col], team_df[away_col])
            team_df[f'opp_{col}'] = np.where(team_df.selection_home == team_name, team_df[away_col], team_df[home_col])

        team_df['is_home'] = np.where(team_df.selection_home == team_name, 1, 0)

        # REPLACE HOME AND AWAY WITH TEAM AND OPPONENT
        team_df['num_tweets'].fillna(0, inplace=True)
        team_df['num_retweets'].fillna(0, inplace=True)
        team_df['sentiment'].fillna(0, inplace=True)
        team_df['opp_num_tweets'].fillna(0, inplace=True)
        team_df['opp_num_retweets'].fillna(0, inplace=True)
        team_df['opp_sentiment'].fillna(0, inplace=True)
        team_df['num_tweets_retweets'] = team_df['num_tweets'] + team_df['num_retweets']
        team_df['opp_num_tweets_retweets'] = team_df['opp_num_tweets'] + team_df['opp_num_retweets']
        team_df['num_tweets_retweets'].fillna(0, inplace=True)
        team_df['opp_num_tweets_retweets'].fillna(0, inplace=True)

        team_df['fan_tweets'].fillna(0, inplace=True)
        team_df['fan_retweets'].fillna(0, inplace=True)
        team_df['fan_sentiment'].fillna(0, inplace=True)
        team_df['opp_fan_tweets'].fillna(0, inplace=True)
        team_df['opp_fan_retweets'].fillna(0, inplace=True)
        team_df['opp_fan_sentiment'].fillna(0, inplace=True)
        team_df['fan_tweets_retweets'] = team_df['fan_tweets'] + team_df['fan_retweets']
        team_df['opp_fan_tweets_retweets'] = team_df['opp_fan_tweets'] + team_df['opp_fan_retweets']
        team_df['fan_tweets_retweets'].fillna(0, inplace=True)
        team_df['opp_fan_tweets_retweets'].fillna(0, inplace=True)

        team_df['hater_tweets'].fillna(0, inplace=True)
        team_df['hater_retweets'].fillna(0, inplace=True)
        team_df['hater_sentiment'].fillna(0, inplace=True)
        team_df['opp_hater_tweets'].fillna(0, inplace=True)
        team_df['opp_hater_retweets'].fillna(0, inplace=True)
        team_df['opp_hater_sentiment'].fillna(0, inplace=True)
        team_df['hater_tweets_retweets'] = team_df['hater_tweets'] + team_df['hater_retweets']
        team_df['opp_hater_tweets_retweets'] = team_df['opp_hater_tweets'] + team_df['opp_hater_retweets']
        team_df['hater_tweets_retweets'].fillna(0, inplace=True)
        team_df['opp_hater_tweets_retweets'].fillna(0, inplace=True)

        goal_diff = np.where(team_df.selection_home == team_name, (team_df['home_score']-team_df['away_score']), (team_df['away_score']-team_df['home_score']))
        # team_df['multiplier'] = np.where(goal_diff >= 0 , goal_diff+1, goal_diff)
        team_df['multiplier'] = np.where(goal_diff < 0 , -1, 1) # change to non-scaled multiplier
        for cue in ['shock', 'surprise', 'sim_shock', 'sim_surprise', 'suspense', 'sim_suspense']:
            team_df[f'own_{cue}'] = team_df[cue] * team_df['multiplier']

        # remove cols, re-order
        columns = ['Course', 'Date', 'time', 'Event ID', 'Inplay flag', 'Market status'] \
                + ['selection', 'opp_selection', 'is_home'] \
                + ['agg_key', 'minute', 'event', 'opp_event', 'event_home'] \
                + ['goal',	'opp_goal', 'score', 'opp_score'] \
                + ['num_tweets', 'num_retweets', 'num_tweets_retweets', 'opp_num_tweets', 'opp_num_retweets', 'opp_num_tweets_retweets'] \
                + ['fan_tweets', 'fan_retweets', 'fan_tweets_retweets', 'opp_fan_tweets', 'opp_fan_retweets', 'opp_fan_tweets_retweets'] \
                + ['hater_tweets', 'hater_retweets', 'hater_tweets_retweets', 'opp_hater_tweets', 'opp_hater_retweets', 'opp_hater_tweets_retweets'] \
                + ['shock', 'surprise', 'suspense'] \
                + ['sim_shock', 'sim_surprise', 'sim_suspense'] \
                + ['multiplier', 'own_shock', 'own_surprise', 'own_sim_shock', 'own_sim_surprise', 'own_suspense', 'own_sim_suspense'] \
                + ['sentiment', 'opp_sentiment'] \
                + ['fan_sentiment', 'opp_fan_sentiment'] \
                + ['hater_sentiment', 'opp_hater_sentiment'] \
                + ['price_match', 'opp_price_match', 'price_match_draw'] \
                + ['prob', 'opp_prob', 'prob_draw'] \
                + ['sim_prob', 'opp_sim_prob', 'sim_prob_draw']

        team_df = team_df[columns]
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

# out_frames['Crystal Palace'].selection = 'C Palace'
# out_frames['C Palace'] = out_frames['C Palace'].append(out_frames['Crystal Palace'])
# del out_frames['Crystal Palace']
for team_name, team_df in out_frames.items():
    outfile = os.path.join(args.output, f'season_2013_agg_final_{team_name}.csv')
    team_df.to_csv(outfile, index=False)
    print(team_name, team_df[['Event ID', 'selection', 'opp_selection']].drop_duplicates().dropna().shape[0])
