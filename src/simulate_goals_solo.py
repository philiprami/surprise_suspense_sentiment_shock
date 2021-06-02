'''
step 3 of calculating suspense
'''

import os
import sys
import time
import json
import argparse
import pandas as pd
from scipy.stats import bernoulli
from collections import defaultdict

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
DATA_DF = pd.read_csv(os.path.join(OUT_DIR, 'season_2013_agg_final_0504.csv'))
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, 'scoring_distribution.csv'), index_col=0)
TRIALS = 100000

# get teams per match
team_df = DATA_DF[['Event ID', 'selection_home', 'selection_away']].drop_duplicates()
team_df['Event ID'] = team_df['Event ID'].astype(int).astype(str)
teams = team_df.set_index('Event ID').T.to_dict()

# get scoring rates
with open(os.path.join(DATA_DIR, 'scoring_rates.json'), 'r') as json_file:
    scoring_rates = json.load(json_file)

parser = argparse.ArgumentParser()
parser.add_argument('-m', required=True)
args = parser.parse_args()
match_id = args.m
print(f'{match_id} queued')

home_team = teams[match_id]['selection_home']
away_team = teams[match_id]['selection_away']
scoring_rate_home = scoring_rates[match_id][home_team]
scoring_rate_away = scoring_rates[match_id][away_team]
match_distrib = DISTRIBUTION.copy()
match_distrib['expctd_goals_home'] = match_distrib['density'] * scoring_rate_home
match_distrib['expctd_goals_away'] = match_distrib['density'] * scoring_rate_away
scorelines = defaultdict(lambda: defaultdict(list))

start = time.perf_counter()
for i in range(TRIALS):
    match_distrib['sim_goals_home'] = match_distrib['expctd_goals_home'].apply(lambda x:bernoulli.rvs(x, size=1)[0])
    match_distrib['sim_goals_away'] = match_distrib['expctd_goals_away'].apply(lambda x:bernoulli.rvs(x, size=1)[0])
    scorelines[match_id]['home'].append(str(match_distrib['sim_goals_home'].sum()))
    scorelines[match_id]['away'].append(str(match_distrib['sim_goals_away'].sum()))

end = time.perf_counter()
print(f'Match {match_id} simulated in {end - start:0.4f} seconds')

with open(os.path.join(SIM_DIR, f'{match_id}_scores.json'), 'w') as json_file:
    json.dump(scorelines, json_file)
