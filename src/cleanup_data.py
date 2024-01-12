import argparse
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = '../data/'
OUT_DIR = DATA_DIR + 'aggregated/'
date_str = datetime.today().strftime('%Y-%m-%d')

def _parse_and_validate_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i',
                        required=True)
    parser.add_argument('--output', '-o',
                        required=True)
    return parser.parse_args()

args = _parse_and_validate_arguments()

INPUT = pd.read_csv(args.input, encoding='utf8')
OUTPUT = pd.DataFrame()

done = set()
event_gb = INPUT.groupby('Event ID')
for match_id, match_df in event_gb:
    if match_id in done:
        continue

    # remove agg_key dups
    dup_mask = match_df.agg_key.duplicated(keep=False)
    if dup_mask.sum() > 0:
        # remove second half match odds
        second_half_mask = match_df.Course.str.contains('Second Half Match Odds') & dup_mask
        if second_half_mask.sum() > 0:
            match_df.drop(index=match_df[second_half_mask].index, inplace=True)

    # remove out of play after game start
    dup_mask = match_df.agg_key.duplicated(keep=False)
    if dup_mask.sum() > 0:
        in_match = match_df[match_df['Inplay flag'] == 1]
        game_start = in_match.iloc[0]['agg_key']
        game_start_stamp = pd.to_datetime(game_start)
        after_start = (pd.to_datetime(match_df.agg_key) >= game_start_stamp) & dup_mask
        after_start_out_of_play = (match_df['Inplay flag'] == 0) & after_start
        match_df = match_df[~after_start_out_of_play]

    # remove twitter draw cols
    match_df.drop(columns=['tweet_sent_mean_draw', 'num_tweets_draw',
                           'num_retweets_draw', 'fan_tweets_draw',
                           'fan_retweets_draw', 'fan_tweet_sent_mean_draw',
                           'hater_tweets_draw', 'hater_retweets_draw',
                           'hater_tweet_sent_mean_draw'],
                  inplace=True)

    # fix twitter times
    match_df.reset_index(drop=True, inplace=True)
    game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
    twitter_actual_start = game_start - timedelta(hours=1)
    pre_match = match_df[match_df.agg_key == str(twitter_actual_start)]
    if pre_match.shape[0] < 1:
        OUTPUT = OUTPUT.append(match_df, ignore_index=True)
        done.add(match_id)
        continue

    twitter_start_index = pre_match.index[0]
    twitter_mask = match_df.tweet_sent_mean_away.notnull() | \
                   match_df.tweet_sent_mean_home.notnull() | \
                   match_df.num_tweets_away.notnull() | \
                   match_df.num_tweets_home.notnull() | \
                   match_df.num_retweets_away.notnull() | \
                   match_df.num_retweets_home.notnull() | \
                   match_df.fan_tweets_away.notnull() | \
                   match_df.fan_tweets_home.notnull() | \
                   match_df.fan_retweets_away.notnull() | \
                   match_df.fan_retweets_home.notnull() | \
                   match_df.fan_tweet_sent_mean_away.notnull() | \
                   match_df.fan_tweet_sent_mean_home.notnull() | \
                   match_df.hater_tweets_away.notnull() | \
                   match_df.hater_tweets_home.notnull() | \
                   match_df.hater_retweets_away.notnull() | \
                   match_df.hater_retweets_home.notnull() | \
                   match_df.hater_tweet_sent_mean_away.notnull() | \
                   match_df.hater_tweet_sent_mean_home.notnull()

    for col in ['tweet_sent_mean_away', 'tweet_sent_mean_home',
                'num_tweets_away', 'num_tweets_home',
                'num_retweets_away', 'num_retweets_home',
                'fan_tweets_away', 'fan_tweets_home',
                'fan_retweets_away', 'fan_retweets_home',
                'fan_tweet_sent_mean_away', 'fan_tweet_sent_mean_home',
                'hater_tweets_home', 'hater_tweets_away',
                'hater_retweets_home', 'hater_retweets_away',
                'hater_tweet_sent_mean_home', 'hater_tweet_sent_mean_away']:
        values = np.array(match_df[twitter_mask][col])
        rows_left = match_df.loc[twitter_start_index:].shape[0]
        if values.shape[0] > rows_left:
            values = values[:rows_left]

        match_df[col] = None
        for i in range(len(values)):
            try:
                match_df.loc[twitter_start_index:match_df.shape[0]-i, col] = values
                break
            except:
                pass

    OUTPUT = OUTPUT.append(match_df, ignore_index=True)
    done.add(match_id)

OUTPUT.to_csv(args.output, index=False)
