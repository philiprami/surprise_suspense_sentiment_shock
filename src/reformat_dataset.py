import os
import sys
import numpy as np
import pandas as pd

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'
same_cols = ['Date', 'time', 'Event ID', 'Course', 'Market status', 'agg_key', 'Inplay flag']

INPUT = pd.read_csv(OUT_DIR + 'season_2013_agg_minute_metrics_0405.csv')
OUTPUT = pd.DataFrame()
gb = INPUT.groupby('Event ID')
for gbi, (match_id, match_df) in enumerate(gb):
    selections = [x for x in match_df.selection.unique() if x != 'The Draw']
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
    merged = home_df.merge(away_df, on=same_cols, how='outer', suffixes=['_home', '_away'])
    merged.sort_values('agg_key', inplace=True)
    for col in ['selection_home', 'selection id_home', 'eff_price_match_home',
               'mean_price_match_home', 'median_price_match_home', 'eff_prob_home',
               'mean_prob_home', 'median_prob_home', 'median_prob-1_home',
               'suspense_mean_prob_home', 'eff_prob-1_home', 'surprise_eff_prob_home',
               'shock_mean_prob_home', 'surprise_mean_prob_home',
               'suspense_median_prob_home', 'surprise_median_prob_home',
               'suspense_eff_prob_home', 'shock_eff_prob_home', 'mean_prob-1_home',
               'shock_median_prob_home', 'selection_away', 'selection id_away',
               'eff_price_match_away', 'mean_price_match_away',
               'median_price_match_away', 'eff_prob_away', 'mean_prob_away',
               'median_prob_away', 'median_prob-1_away', 'suspense_mean_prob_away',
               'eff_prob-1_away', 'surprise_eff_prob_away', 'shock_mean_prob_away',
               'surprise_mean_prob_away', 'suspense_median_prob_away',
               'surprise_median_prob_away', 'suspense_eff_prob_away',
               'shock_eff_prob_away', 'mean_prob-1_away', 'shock_median_prob_away']:
        merged[col] = merged[col].ffill()

    OUTPUT = OUTPUT.append(merged)

    if gbi % 100 == 0:
        OUTPUT.to_csv(OUT_DIR + 'season_2013_agg_final_0405.csv', index=False)
