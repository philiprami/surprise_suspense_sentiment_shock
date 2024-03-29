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

# calculate implicit prob first
for price_col, prob_col in zip(price_cols, prob_cols):
    for outcome in outcomes:
        INPUT[f'{prob_col}_{outcome}'] = 1/INPUT[f'{price_col}_{outcome}']

#  scale prices to remove overround
done = set()
event_gb = INPUT.groupby('Event ID')
for match_id, match_df in event_gb:
    if match_id in done:
        continue

    print(match_id)
    for i, row in match_df.iterrows():
        for prob_col in prob_cols:
            cols = [f'{prob_col}_{outcome}' for outcome in outcomes]
            total = sum([row[col] for col in cols])
            for col in cols:
                row[col] = row[col]/total

        OUTPUT = OUTPUT.append(row, ignore_index=True)

    done.add(match_id)

OUTPUT.to_csv(args.output, index=False)
