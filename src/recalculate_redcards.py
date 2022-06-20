import os
import re
import sys
import json
import math
import logging
import argparse
import pandas as pd
from datetime import datetime
from operator import itemgetter
from scipy.stats import bernoulli

TRIALS = 100000
DIR = os.path.dirname(os.path.realpath(__file__))
DATA_DIR = os.path.join(DIR, '../data')
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, 'scoring_distribution.csv'), index_col=0)

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
DATA_DF = pd.read_csv(args.input)

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
        for col in ['eff']:
            first_half = True
            minute = 0
            for index, row in match_df.iterrows():
                if index == start_index-1:
                    home_simulations = sims_h.sum()
                    away_simulations = sims_a.sum()
                    sim_home_w_prob = (home_simulations > away_simulations).sum() / home_simulations.shape[0]
                    sim_away_w_prob = (home_simulations < away_simulations).sum() / home_simulations.shape[0]
                    sim_draw_prob = (home_simulations == away_simulations).sum() / home_simulations.shape[0]
                    DATA_DF.loc[index, 'sim_home_prob'] = sim_home_w_prob
                    DATA_DF.loc[index, 'sim_away_prob'] = sim_away_w_prob
                    DATA_DF.loc[index, 'sim_draw_prob'] = sim_draw_prob
                    continue
                if index < start_index:
                    continue
                if index >= half_index:
                    first_half = False

                home_score = home_scores.loc[index]
                away_score = away_scores.loc[index]

                # simulations given current scores
                home_simulations = sims_h.iloc[minute+1:].sum() + home_score
                away_simulations = sims_a.iloc[minute+1:].sum() + away_score
                sim_home_w_prob = (home_simulations > away_simulations).sum() / home_simulations.shape[0]
                sim_away_w_prob = (home_simulations < away_simulations).sum() / home_simulations.shape[0]
                sim_draw_prob = (home_simulations == away_simulations).sum() / home_simulations.shape[0]
                DATA_DF.loc[index, 'sim_home_prob'] = sim_home_w_prob
                DATA_DF.loc[index, 'sim_away_prob'] = sim_away_w_prob
                DATA_DF.loc[index, 'sim_draw_prob'] = sim_draw_prob

                # simulations given a simulated home score and current scores
                next_minute_score_home = sims_h.T[sims_h.T[minute+1] > 0].index
                prob_next_min_home_score = next_minute_score_home.shape[0] / sims_h.T.shape[0]
                home_score_home_simulations = sims_h.iloc[minute+1:][next_minute_score_home].sum() + home_score
                home_score_away_simulations = sims_a.iloc[minute+1:][next_minute_score_home].sum() + away_score
                home_score_home_prob = (home_score_home_simulations > home_score_away_simulations).sum() / next_minute_score_home.shape[0]
                home_score_away_prob = (home_score_home_simulations < home_score_away_simulations).sum() / next_minute_score_home.shape[0]
                home_score_draw_prob = (home_score_home_simulations == home_score_away_simulations).sum() / next_minute_score_home.shape[0]

                sim_home_score_home_sq_diff = math.pow((home_score_home_prob-sim_home_w_prob), 2)
                sim_home_score_away_sq_diff = math.pow((home_score_away_prob-sim_away_w_prob), 2)
                sim_home_score_draw_sq_diff = math.pow((home_score_draw_prob-sim_draw_prob), 2)
                sim_home_score_sums = (prob_next_min_home_score*sim_home_score_home_sq_diff)+\
                  (prob_next_min_home_score*sim_home_score_away_sq_diff)+\
                    (prob_next_min_home_score*sim_home_score_draw_sq_diff)

                # simulations w/ real odds given a simulated home score and current scores
                home_score_home_sq_diff = math.pow((home_score_home_prob-row[f'{col}_prob_home']), 2)
                home_score_away_sq_diff = math.pow((home_score_away_prob-row[f'{col}_prob_away']), 2)
                home_score_draw_sq_diff = math.pow((home_score_draw_prob-row[f'{col}_prob_draw']), 2)
                home_score_sums = (prob_next_min_home_score*home_score_home_sq_diff)+\
                  (prob_next_min_home_score*home_score_away_sq_diff)+\
                    (prob_next_min_home_score*home_score_draw_sq_diff)

                # simulations given a simulated away score and current scores
                next_minute_score_away = sims_a.T[sims_a.T[minute+1] > 0].index
                prob_next_min_away_score = next_minute_score_away.shape[0] / sims_a.T.shape[0]
                away_score_home_simulations = sims_h.iloc[minute+1:][next_minute_score_away].sum() + home_score
                away_score_away_simulations = sims_a.iloc[minute+1:][next_minute_score_away].sum() + away_score
                away_score_home_prob = (away_score_home_simulations > away_score_away_simulations).sum() / next_minute_score_away.shape[0]
                away_score_away_prob = (away_score_home_simulations < away_score_away_simulations).sum() / next_minute_score_away.shape[0]
                away_score_draw_prob = (away_score_home_simulations == away_score_away_simulations).sum() / next_minute_score_away.shape[0]

                sim_away_score_home_sq_diff = math.pow((away_score_home_prob-sim_home_w_prob), 2)
                sim_away_score_away_sq_diff = math.pow((away_score_away_prob-sim_away_w_prob), 2)
                sim_away_score_draw_sq_diff = math.pow((away_score_draw_prob-sim_draw_prob), 2)
                sim_away_score_sums = (prob_next_min_away_score*sim_away_score_home_sq_diff)+\
                  (prob_next_min_away_score*sim_away_score_away_sq_diff)+\
                    (prob_next_min_away_score*sim_away_score_draw_sq_diff)

                # simulations w/ real odds given a simulated away score and current scores
                away_score_home_sq_diff = math.pow((away_score_home_prob-row[f'{col}_prob_home']), 2)
                away_score_away_sq_diff = math.pow((away_score_away_prob-row[f'{col}_prob_away']), 2)
                away_score_draw_sq_diff = math.pow((away_score_draw_prob-row[f'{col}_prob_draw']), 2)
                away_score_sums = (prob_next_min_away_score*away_score_home_sq_diff)+\
                  (prob_next_min_away_score*away_score_away_sq_diff)+\
                    (prob_next_min_away_score*away_score_draw_sq_diff)

                # sum the sums, raise to the power 1/2
                suspense = math.sqrt(home_score_sums+away_score_sums)
                sim_suspense = math.sqrt(sim_home_score_sums+sim_away_score_sums)
                logging.info(f'agg key {row.agg_key}. minute: {minute}. suspense: {round(suspense, 3)}. simulated suspense: {round(sim_suspense, 3)}')
                if first_half and minute < 45:
                    minute += 1
                if not first_half and minute < 91:
                    minute += 1

                DATA_DF.loc[index, f'suspense_{col}_prob'] = suspense
                DATA_DF.loc[index, f'sim_suspense'] = sim_suspense

    done.add(match_id)

DATA_DF.to_csv(args.output, index=False)
