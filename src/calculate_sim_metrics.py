import os
import sys
import logging
import argparse
import pandas as pd
from math import sqrt, pow
from datetime import datetime
from collections import defaultdict

DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(DIR, '../data')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')

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
INPUT = pd.read_csv(args.input)
OUTPUT = pd.DataFrame()

done = set()
event_gb = INPUT.groupby('Event ID')
for match_id, match_df in event_gb:
    if match_id in done:
        continue

    print(match_id)
    match_df.sort_values('agg_key', inplace=True)
    pre_match = match_df['Inplay flag'] == 0
    pre_match_probs = {}
    sim_cols = ['sim_home_prob', 'sim_away_prob', 'sim_draw_prob']
    for col in sim_cols:
        match_df[f'{col}-1'] = match_df[col].shift(1)
        pre_match_probs[col] = match_df[~pre_match].iloc[0][col]

    surprise = ((match_df['sim_home_prob'] - match_df['sim_home_prob-1']).apply(lambda x: pow(x, 2)) + \
                (match_df['sim_away_prob'] - match_df['sim_away_prob-1']).apply(lambda x: pow(x, 2)) + \
                (match_df['sim_draw_prob'] - match_df['sim_draw_prob-1']).apply(lambda x: pow(x, 2)))\
                .apply(lambda x: sqrt(x))

    shock = ((match_df['sim_home_prob'] - pre_match_probs['sim_home_prob']).apply(lambda x: pow(x, 2)) + \
             (match_df['sim_away_prob'] - pre_match_probs['sim_away_prob']).apply(lambda x: pow(x, 2)) + \
             (match_df['sim_draw_prob'] - pre_match_probs['sim_draw_prob']).apply(lambda x: pow(x, 2)))\
             .apply(lambda x: sqrt(x))

    match_df[f'sim_surprise'] = surprise
    match_df[f'sim_shock'] = shock

    OUTPUT = OUTPUT.append(match_df, ignore_index=True)
    done.add(match_id)

OUTPUT.to_csv(args.output, index=False)
