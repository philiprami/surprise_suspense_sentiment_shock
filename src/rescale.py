import sys
import pandas as pd
from math import sqrt, pow
from collections import defaultdict

DATA_DIR = '../data/'
OUT_DIR = DATA_DIR + 'aggregated/'
price_cols = ['eff_price_match', 'mean_price_match', 'median_price_match']
prob_cols = ['eff_prob', 'mean_prob', 'median_prob']
outcomes = ['home', 'away', 'draw']

INPUT = pd.read_csv(OUT_DIR + 'season_2013_agg_sec_reformatted_0811.csv')
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

OUTPUT.to_csv(OUT_DIR + 'season_2013_agg_sec_scaled_0811.csv', index=False)
