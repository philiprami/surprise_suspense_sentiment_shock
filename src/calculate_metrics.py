import sys
from math import sqrt, pow
from collections import defaultdict
import pandas as pd

DATA_DIR = '../data/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'
price_cols = ['eff_price_match', 'mean_price_match', 'median_price_match']
prob_cols = ['eff_prob', 'mean_prob', 'median_prob']
results = pd.read_csv(OUT_DIR + 'season_2013_agg_event_twitter_3103.csv')

# first iteration... scale prices to remove overround
print('first iteration')
first_done = set()
for price_col, prob_col in zip(price_cols, prob_cols):
    results[prob_col] = 1/results[price_col]

event_gb = results.groupby('Event ID')
for match_id, match_df in event_gb:
    if match_id in first_done:
        continue

    print(match_id)
    sel_frames = {x:y for x,y in match_df.groupby('selection')}
    if len(sel_frames) != 3:
        sys.exit('selection missing')

    title = match_df['Course'].mode()[0]
    matchup = title.split(':')[-2]
    away, home = [x.strip() for x in matchup.split(' v ')]
    draw = (set(sel_frames.keys()) - set([home, away])).pop()

    agg_keys = set([agg_key for frame in sel_frames.values() for agg_key in frame.agg_key.unique()])
    for agg_key in sorted(list(agg_keys)):
        away_mask = sel_frames[away]['agg_key'] == agg_key
        home_mask = sel_frames[home]['agg_key'] == agg_key
        draw_mask = sel_frames[draw]['agg_key'] == agg_key
        if away_mask.sum() != 1 or home_mask.sum() != 1 or draw_mask.sum() != 1:
            continue
        else:
            away_row = sel_frames[away][away_mask].iloc[0]
            home_row = sel_frames[home][home_mask].iloc[0]
            draw_row = sel_frames[draw][draw_mask].iloc[0]
            for col in prob_cols:
                away_prob = away_row[col]
                home_prob = home_row[col]
                draw_prob = draw_row[col]
                total = away_prob + home_prob + draw_prob
                away_prob = (away_prob/total)*1
                home_prob = (home_prob/total)*1
                draw_prob = (draw_prob/total)*1
                away_row[col] = away_prob
                home_row[col] = home_prob
                draw_row[col] = draw_prob

            for row in [away_row, home_row, draw_row]:
                results.loc[row.name] = row

    first_done.add(match_id)

# second iteration... calculate metrics
second_done = set()
event_gb = results.groupby('Event ID')
for match_id, match_df in event_gb:
    if match_id in second_done:
        continue

    print(match_id)
    sel_frames = {x:y for x,y in match_df.groupby('selection')}
    if len(sel_frames) != 3:
        sys.exit('selection missing')

    title = match_df['Course'].mode()[0]
    matchup = title.split(':')[-2]
    away, home = [x.strip() for x in matchup.split(' v ')]
    draw = (set(sel_frames.keys()) - set([home, away])).pop()

    try:
        pre_match_probs = defaultdict(dict)
        for key in sel_frames:
            for col in prob_cols:
                sel_frames[key] = sel_frames[key].sort_values('agg_key')
                sel_frames[key][f'{col}-1'] = sel_frames[key][col].shift(1)
                pre_match_probs[key][col] = sel_frames[key][sel_frames[key]['Inplay flag'] == 0].iloc[-1][col]
    except:
        continue

    agg_keys = set([agg_key for frame in sel_frames.values() for agg_key in frame.agg_key.unique()])
    for agg_key in sorted(list(agg_keys)):
        away_mask = sel_frames[away]['agg_key'] == agg_key
        home_mask = sel_frames[home]['agg_key'] == agg_key
        draw_mask = sel_frames[draw]['agg_key'] == agg_key
        if away_mask.sum() != 1 or home_mask.sum() != 1 or draw_mask.sum() != 1:
            continue
        else:
            away_row = sel_frames[away][away_mask].iloc[0]
            home_row = sel_frames[home][home_mask].iloc[0]
            draw_row = sel_frames[draw][draw_mask].iloc[0]
            for col in prob_cols:
                surprise = sqrt(pow((home_row[col] - home_row[f'{col}-1']), 2) + \
                  pow((draw_row[col] - draw_row[f'{col}-1']), 2) + \
                    pow((away_row[col] - away_row[f'{col}-1']), 2))
                shock = sqrt(pow((home_row[col] - pre_match_probs[home][col]), 2) + \
                  pow((draw_row[col] - pre_match_probs[draw][col]), 2) + \
                    pow((away_row[col] - pre_match_probs[away][col]), 2))
                suspense = None

                for row in [away_row, home_row, draw_row]:
                    row[f'surprise_{col}'] = surprise
                    row[f'shock_{col}'] = shock
                    row[f'suspense_{col}'] = suspense

            for row in [away_row, home_row, draw_row]:
                cols_left = set(row.index) - set(results.columns)
                if len(cols_left):
                    for col in cols_left:
                        results.loc[row.name, col] = row[col]
                else:
                    results.loc[row.name] = row

    second_done.add(match_id)

results.to_csv(OUT_DIR + 'season_2013_agg_minute_metrics_0405.csv', index=False)
