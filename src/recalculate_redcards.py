import os
import re
import json
import math
import pandas as pd
from operator import itemgetter
from scipy.stats import bernoulli

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
COMM_DIR = os.path.join(DATA_DIR, 'commentaries/season_2013_match_part1')
DATA_DF = pd.read_csv(os.path.join(OUT_DIR, 'season_2013_complete_0706.csv'))
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, 'scoring_distribution.csv'), index_col=0)

TRIALS = 100000

# get teams per match
team_df = DATA_DF[['Event ID', 'selection_home', 'selection_away']].drop_duplicates()
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
        home_scores = match_df.event_home.fillna('').apply(lambda x: len(re.findall('goal', x))).cumsum()
        away_scores = match_df.event_away.fillna('').apply(lambda x: len(re.findall('goal', x))).cumsum()
        minute = 0
        for index, row in match_df.iterrows():
            if minute > 92:
                break
            if row['Inplay flag'] == 0:
                continue

            home_score = home_scores.loc[index]
            away_score = away_scores.loc[index]
            for col in ['eff', 'mean', 'median']:
                # simulations given a simulated home score and current scores
                minute_score_home = sims_h.T[sims_h.T[minute] > 0].index
                home_simulations = sims_h.iloc[minute:][minute_score_home].sum() + home_score
                away_simulations = sims_a.iloc[minute:][minute_score_home].sum() + away_score
                home_w_prob = (home_simulations > away_simulations).sum() / minute_score_home.shape[0]
                away_w_prob = (home_simulations < away_simulations).sum() / minute_score_home.shape[0]
                draw_prob = (home_simulations == away_simulations).sum() / minute_score_home.shape[0]
                home_sq_diff = (home_w_prob-row[f'{col}_prob_home'])*(home_w_prob-row[f'{col}_prob_home'])
                away_sq_diff = (away_w_prob-row[f'{col}_prob_away'])*(away_w_prob-row[f'{col}_prob_away'])
                draw_sq_diff = (draw_prob-row[f'{col}_prob_draw'])*(draw_prob-row[f'{col}_prob_draw'])
                home_score_sum = home_sq_diff+away_sq_diff+draw_sq_diff

                # simulations given a simulated away score and current scores
                minute_score_away = sims_a.T[sims_a.T[minute] > 0].index
                home_simulations = sims_h.iloc[minute:][minute_score_away].sum() + home_score
                away_simulations = sims_a.iloc[minute:][minute_score_away].sum() + away_score
                home_w_prob = (home_simulations > away_simulations).sum() / minute_score_away.shape[0]
                away_w_prob = (home_simulations < away_simulations).sum() / minute_score_away.shape[0]
                draw_prob = (home_simulations == away_simulations).sum() / minute_score_away.shape[0]
                home_sq_diff = (home_w_prob-row[f'{col}_prob_home'])*(home_w_prob-row[f'{col}_prob_home'])
                away_sq_diff = (away_w_prob-row[f'{col}_prob_away'])*(away_w_prob-row[f'{col}_prob_away'])
                draw_sq_diff = (draw_prob-row[f'{col}_prob_draw'])*(draw_prob-row[f'{col}_prob_draw'])
                away_score_sum = home_sq_diff+away_sq_diff+draw_sq_diff

                # sum the sums, raise to the power 1/2
                suspense = math.sqrt(home_score_sum+away_score_sum)
                DATA_DF.loc[index, f'suspense_{col}_prob'] = suspense

            minute += 1

    done.add(match_id)

DATA_DF.to_csv(os.path.join(OUT_DIR, 'season_2013_complete_redcard_0706.csv'), index=False)
