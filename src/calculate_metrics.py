import argparse
import sys
import pandas as pd
from math import sqrt, pow
from datetime import datetime
from collections import defaultdict

DATA_DIR = '../data/'
OUT_DIR = DATA_DIR + 'aggregated/'
price_cols = ['eff_price_match', 'mean_price_match', 'median_price_match']
prob_cols = ['eff_prob', 'mean_prob', 'median_prob']
outcomes = ['home', 'away', 'draw']

date_str = datetime.today().strftime('%Y-%m-%d')

def _parse_and_validate_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i',
                        required=True)
    parser.add_argument('--output', '-o',
                        required=True)
    return parser.parse_args()

args = _parse_and_validate_arguments()

INPUT = pd.read_csv(args.input)
OUTPUT = pd.DataFrame()

done = set()
event_gb = INPUT.groupby('Event ID')
for match_id, match_df in event_gb:
    if match_id in done:
        continue

    print(match_id)
    match_df.sort_values('agg_key', inplace=True)
    pre_match = match_df[match_df['Inplay flag'] == 0]
    pre_match_probs = {}
    for prob_col in prob_cols:
        cols = [f'{prob_col}_{outcome}' for outcome in outcomes]
        for col in cols:
            match_df[f'{col}-1'] = match_df[col].shift(1)
            if pre_match.shape[0] > 0:
                pre_match_probs[col] = pre_match.iloc[-1][col]
            else:
                pre_match_probs[col] = None

    for prob_col in prob_cols:
        surprise = ((match_df[f'{prob_col}_home'] - match_df[f'{prob_col}_home-1']).apply(lambda x: pow(x, 2)) + \
                    (match_df[f'{prob_col}_away'] - match_df[f'{prob_col}_away-1']).apply(lambda x: pow(x, 2)) + \
                    (match_df[f'{prob_col}_draw'] - match_df[f'{prob_col}_draw-1']).apply(lambda x: pow(x, 2)))\
                    .apply(lambda x: sqrt(x))

        if pre_match.shape[0] > 0:
            shock = ((match_df[f'{prob_col}_home'] - pre_match_probs[f'{prob_col}_home']).apply(lambda x: pow(x, 2)) + \
                     (match_df[f'{prob_col}_away'] - pre_match_probs[f'{prob_col}_away']).apply(lambda x: pow(x, 2)) + \
                     (match_df[f'{prob_col}_draw'] - pre_match_probs[f'{prob_col}_draw']).apply(lambda x: pow(x, 2)))\
                     .apply(lambda x: sqrt(x))
        else:
            shock = None

        suspense = None
        match_df[f'surprise_{prob_col}'] = surprise
        match_df[f'shock_{prob_col}'] = shock
        match_df[f'suspense_{prob_col}'] = suspense

    OUTPUT = OUTPUT.append(match_df, ignore_index=True)
    done.add(match_id)

OUTPUT.to_csv(args.output, index=False)
