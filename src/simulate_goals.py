'''
step 3 of calculating suspense
'''

import os
import sys
import json
import pandas as pd
from queue import Queue
from threading import Thread
from operator import itemgetter
from scipy.stats import bernoulli

TRIALS = 100000

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
DATA_DF = pd.read_csv(os.path.join(OUT_DIR, 'season_2013_agg_final_0504.csv'))
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, 'scoring_distribution.csv'), index_col=0)

# get teams per match
team_df = DATA_DF[['Event ID', 'selection_home', 'selection_away']].drop_duplicates()
team_df['Event ID'] = team_df['Event ID'].astype(int).astype(str)
teams = team_df.set_index('Event ID').T.to_dict()

# get scoring rates
with open(os.path.join(DATA_DIR, 'scoring_rates.json'), 'r') as json_file:
    scoring_rates = json.load(json_file)

def simulate(match_id):
    home_team = teams[match_id]['selection_home']
    away_team = teams[match_id]['selection_away']
    scoring_rate_home = scoring_rates[match_id][home_team]
    scoring_rate_away = scoring_rates[match_id][away_team]
    match_distrib = DISTRIBUTION.copy()
    match_distrib['expctd_goals_home'] = match_distrib['density'] * scoring_rate_home
    match_distrib['expctd_goals_away'] = match_distrib['density'] * scoring_rate_away
    home = match_distrib['expctd_goals_home'].apply(lambda x:bernoulli.rvs(x, size=TRIALS)).transform({f'{i}': itemgetter(i) for i in range(TRIALS)})
    away = match_distrib['expctd_goals_away'].apply(lambda x:bernoulli.rvs(x, size=TRIALS)).transform({f'{i}': itemgetter(i) for i in range(TRIALS)})
    home.loc['score'] = home.sum()
    away.loc['score'] = away.sum()
    home_file = os.path.join(SIM_DIR, f'{match_id}_home.csv')
    away_file = os.path.join(SIM_DIR, f'{match_id}_away.csv')
    home.to_csv(home_file)
    away.to_csv(away_file)
    return

# multithread simulations
print('queueing matches')
q = Queue()
for match_id in scoring_rates:
    if os.path.isfile(os.path.join(SIM_DIR, f'{match_id}_home.csv')):
        continue
    q.put(match_id)
q.put(None)

def worker():
    while True:
        match_id = q.get()
        print(f'performing simulations for match {match_id}')
        if match_id is None:
          return

        simulate(match_id)

print('done queing, starting workers...')
num_workers = 5
threads = [Thread(target=worker) for _i in range(num_workers)]
for thread in threads:
    thread.start()
