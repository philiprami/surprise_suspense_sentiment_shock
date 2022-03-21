import os
import re
import json
import math
import pandas as pd
from datetime import datetime
from operator import itemgetter
from scipy.stats import bernoulli

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
date_str = datetime.today().strftime('%Y-%m-%d')
DATA_DF = pd.read_csv(os.path.join(OUT_DIR, f'season_2013_agg_suspense_{date_str}.csv'))
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, 'scoring_distribution.csv'), index_col=0)

TRIALS = 100000

# get teams per match
team_df = DATA_DF[['Event ID', 'selection_home', 'selection_away']].dropna().drop_duplicates()
team_df['Event ID'] = team_df['Event ID'].astype(int).astype(str)
teams = team_df.set_index('Event ID').T.to_dict()

with open(os.path.join(DATA_DIR, 'scoring_rates.json'), 'r') as json_file:
    scoring_rates = json.load(json_file)

done = set()
for match_id, match_df in DATA_DF.groupby('Event ID'):
    match_id = str(int(match_id))
    if match_id in done:
        print(f'{match_id} already done. skipping.')
        continue

    red_card_home = match_df['event_home'].fillna('').str.contains('red card', case=False)
    red_card_away = match_df['event_away'].fillna('').str.contains('red card', case=False)
    if red_card_home.sum() > 0 or red_card_away.sum() > 0:
        print(f'red card found: re-calculating {match_id}')

        home_team = teams[match_id]['selection_home']
        away_team = teams[match_id]['selection_away']
        scoring_rate_home = scoring_rates[match_id][home_team]
        scoring_rate_away = scoring_rates[match_id][away_team]
        match_distrib = DISTRIBUTION.copy()
        match_distrib['scoring_rate_home'] = scoring_rate_home
        match_distrib['scoring_rate_away'] = scoring_rate_away

        # adjust distribution according to red cards
        minute = 0
        for index, row in match_df.fillna('').iterrows():
            if minute > 92:
                break
            if row['Inplay flag'] == 0:
                continue

            if 'red card' in row['event_home']:
                match_distrib.loc[minute:, 'scoring_rate_home'] = match_distrib.iloc[minute:]['scoring_rate_home'] * (2/3.)
                match_distrib.loc[minute:, 'scoring_rate_away'] = match_distrib.iloc[minute:]['scoring_rate_away'] * 1.2

            if 'red card' in row['event_away']:
                match_distrib.loc[minute:, 'scoring_rate_away'] = match_distrib.iloc[minute:]['scoring_rate_away'] * (2/3.)
                match_distrib.loc[minute:, 'scoring_rate_home'] = match_distrib.iloc[minute:]['scoring_rate_home'] * 1.2

            minute += 1

        match_distrib['expctd_goals_home'] = match_distrib['density'] * match_distrib['scoring_rate_home']
        match_distrib['expctd_goals_away'] = match_distrib['density'] * match_distrib['scoring_rate_away']

        # re-simulate
        sims_h = match_distrib['expctd_goals_home'].apply(lambda x:bernoulli.rvs(x, size=TRIALS)).transform({f'{i}': itemgetter(i) for i in range(TRIALS)})
        sims_a = match_distrib['expctd_goals_away'].apply(lambda x:bernoulli.rvs(x, size=TRIALS)).transform({f'{i}': itemgetter(i) for i in range(TRIALS)})

        # re-calculate suspense
        start_index = match_df[match_df.event_home.fillna('').str.contains('start')].iloc[0].name
        half_index = match_df[match_df.event_home.fillna('').str.contains('start')].iloc[1].name
        home_goals = match_df.event_home.fillna('').apply(lambda x: len(re.findall('goal', x))).cumsum()
        away_goals = match_df.event_away.fillna('').apply(lambda x: len(re.findall('goal', x))).cumsum()
        home_own_goals = match_df.event_home.fillna('').apply(lambda x: len(re.findall('own goal', x))).cumsum()
        away_own_goals = match_df.event_away.fillna('').apply(lambda x: len(re.findall('own goal', x))).cumsum()
        home_scores = home_goals - home_own_goals + away_own_goals
        away_scores = away_goals - away_own_goals + home_own_goals
        for col in ['eff', 'mean', 'median']:
            first_half = True
            minute = 0
            for index, row in match_df.iterrows():
                if index < start_index:
                    continue
                if index >= half_index:
                    first_half = False

                home_score = home_scores.loc[index]
                away_score = away_scores.loc[index]
                # simulations given a simulated home score and current scores
                next_minute_score_home = sims_h.T[sims_h.T[minute+1] > 0].index
                prob_next_min_home_score = next_minute_score_home.shape[0] / sims_h.T.shape[0]
                home_simulations = sims_h.iloc[minute+1:][next_minute_score_home].sum() + home_score
                away_simulations = sims_a.iloc[minute+1:][next_minute_score_home].sum() + away_score
                home_w_prob = (home_simulations > away_simulations).sum() / next_minute_score_home.shape[0]
                away_w_prob = (home_simulations < away_simulations).sum() / next_minute_score_home.shape[0]
                draw_prob = (home_simulations == away_simulations).sum() / next_minute_score_home.shape[0]
                home_sq_diff = math.pow((home_w_prob-row[f'{col}_prob_home']), 2)
                away_sq_diff = math.pow((away_w_prob-row[f'{col}_prob_away']), 2)
                draw_sq_diff = math.pow((draw_prob-row[f'{col}_prob_draw']), 2)
                home_score_sums = (prob_next_min_home_score*home_sq_diff)+\
                  (prob_next_min_home_score*away_sq_diff)+\
                    (prob_next_min_home_score*draw_sq_diff)

                # simulations given a simulated away score and current scores
                next_minute_score_away = sims_a.T[sims_a.T[minute+1] > 0].index
                prob_next_min_away_score = next_minute_score_away.shape[0] / sims_a.T.shape[0]
                home_simulations = sims_h.iloc[minute+1:][next_minute_score_away].sum() + home_score
                away_simulations = sims_a.iloc[minute+1:][next_minute_score_away].sum() + away_score
                home_w_prob = (home_simulations > away_simulations).sum() / next_minute_score_away.shape[0]
                away_w_prob = (home_simulations < away_simulations).sum() / next_minute_score_away.shape[0]
                draw_prob = (home_simulations == away_simulations).sum() / next_minute_score_away.shape[0]
                home_sq_diff = math.pow((home_w_prob-row[f'{col}_prob_home']), 2)
                away_sq_diff = math.pow((away_w_prob-row[f'{col}_prob_away']), 2)
                draw_sq_diff = math.pow((draw_prob-row[f'{col}_prob_draw']), 2)
                away_score_sums = (prob_next_min_away_score*home_sq_diff)+\
                  (prob_next_min_away_score*away_sq_diff)+\
                    (prob_next_min_away_score*draw_sq_diff)

                # sum the sums, raise to the power 1/2
                suspense = math.sqrt(home_score_sums+away_score_sums)
                DATA_DF.loc[index, f'suspense_{col}_prob'] = suspense

                if first_half and minute < 45:
                    minute += 1
                if not first_half and minute < 91:
                    minute += 1

    done.add(match_id)

DATA_DF.to_csv(os.path.join(OUT_DIR, f'season_2013_agg_final_{date_str}.csv'), index=False)
