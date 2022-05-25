import os
import gc
import re
import sys
import math
import logging
import argparse
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)],
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%m-%d-%y %H:%M:%S')

def _parse_and_validate_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i',
                        required=True)
    parser.add_argument('--output', '-o',
                        required=True)
    return parser.parse_args()

args = _parse_and_validate_arguments()
df = pd.read_csv(args.input)

# remove
med_cols = [x for x in df.columns if 'median_' in x]
mean_cols = [x for x in df.columns if 'mean_' in x and 'tweet' not in x]
shift_cols = [x for x in df.columns if '-1' in x]
df = df[[x for x in df.columns if x not in med_cols]]
df = df[[x for x in df.columns if x not in mean_cols]]
df = df[[x for x in df.columns if x not in shift_cols]]

# rename
rename_cols = {x : x.replace('eff_', '') for x in df.columns if 'eff' in x}
rename_cols = {x: y.replace('_prob', '') for x,y in rename_cols.items()}
rename_cols['tweet_sent_mean_home'] = 'sentiment_home'
rename_cols['tweet_sent_mean_away'] = 'sentiment_away'
rename_cols['fan_tweet_sent_mean_home'] = 'fan_sentiment_home'
rename_cols['fan_tweet_sent_mean_away'] = 'fan_sentiment_away'
rename_cols['hater_tweet_sent_mean_home'] = 'hater_sentiment_home'
rename_cols['hater_tweet_sent_mean_away'] = 'hater_sentiment_away'
rename_cols['sim_home_prob'] = 'sim_prob_home'
rename_cols['sim_away_prob'] = 'sim_prob_away'
rename_cols['sim_draw_prob'] = 'sim_prob_draw'
df.rename(columns=rename_cols, inplace=True)

# re-order
columns = ['Course', 'Date', 'time', 'Event ID', 'Inplay flag', 'Market status'] \
        + ['selection_home', 'selection_away'] \
        + ['agg_key', 'minute', 'event_home', 'event_away'] \
        + ['home_goal',	'away_goal', 'home_score', 'away_score'] \
        + ['num_tweets_home', 'num_retweets_home', 'num_tweets_away', 'num_retweets_away'] \
        + ['fan_tweets_home', 'fan_retweets_home', 'fan_tweets_away', 'fan_retweets_away'] \
        + ['hater_tweets_home', 'hater_retweets_home', 'hater_tweets_away', 'hater_retweets_away'] \
        + ['shock', 'surprise', 'suspense'] \
        + ['sim_shock', 'sim_surprise', 'sim_suspense'] \
        + ['sentiment_home', 'sentiment_away'] \
        + ['fan_sentiment_home', 'fan_sentiment_away'] \
        + ['hater_sentiment_home', 'hater_sentiment_away'] \
        + ['price_match_home', 'price_match_away', 'price_match_draw'] \
        + ['prob_home', 'prob_away', 'prob_draw'] \
        + ['sim_prob_home', 'sim_prob_away', 'sim_prob_draw']

df = df[columns]
df.to_csv(args.output, index=False)
