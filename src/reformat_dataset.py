import os
import sys
import numpy as np
import pandas as pd
from datetime import datetime

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'
same_cols = ['Date', 'time', 'Event ID', 'Course', 'Market status', 'agg_key', 'Inplay flag']
date_str = datetime.today().strftime('%Y-%m-%d')

INPUT = pd.read_csv(OUT_DIR + f'season_2013_agg_min_2022-03-23.csv')
OUTPUT = pd.DataFrame()
gb = INPUT.groupby('Event ID')
for gbi, (match_id, match_df) in enumerate(gb):
    selections = [x for x in match_df.selection.unique() if x != 'The Draw']
    if len(selections) != 2:
        continue
    event = match_df['Course'].all()
    selection_i = [event.index(x) for x in selections]
    for selection, index in zip(selections, selection_i):
        other_index = [i for i in selection_i if i != index][0]
        if index < other_index:
            home = selection
            away = [x for x in selections if x != selection][0]
        else:
            home =[x for x in selections if x != selection][0]
            away = selection
        break

    home_df = match_df[match_df.selection == home]
    away_df = match_df[match_df.selection == away]
    draw_df = match_df[match_df.selection == 'The Draw']
    merged = home_df.merge(away_df, on=same_cols, how='outer', suffixes=['_home', '_away'])
    merged = merged.merge(draw_df, on=same_cols, how='outer')
    merged.rename(columns={x:f'{x}_draw' for x in set(draw_df.columns) - set(same_cols)}, inplace=True)
    merged.sort_values('agg_key', inplace=True)
    for outcome_suffix in ['_home', '_away', '_draw']:
        for col in ['selection', 'selection id', 'eff_price_match',
                    'mean_price_match', 'median_price_match']:
            merged[f'{col}{outcome_suffix}'] = merged[f'{col}{outcome_suffix}'].bfill()

    OUTPUT = OUTPUT.append(merged)

    if gbi % 100 == 0:
        OUTPUT.to_csv(OUT_DIR + f'season_2013_agg_reformatted_{date_str}.csv', index=False)

OUTPUT.to_csv(OUT_DIR + f'season_2013_agg_reformatted_{date_str}.csv', index=False)
