import os
import re
import sys
import json
import math
import logging
import numpy as np
import pandas as pd
from operator import itemgetter
from scipy.stats import bernoulli

logging.basicConfig(level=logging.INFO,
                    handlers=[logging.StreamHandler(sys.stdout)],
                    format='%(asctime)s %(levelname)s - %(message)s',
                    datefmt='%m-%d-%y %H:%M:%S')

DATA_DIR = '/Users/philipramirez/school/surprise_suspense_sentiment/data/aggregated'
SIM_DIR = os.path.join(DATA_DIR, '../simulations')
with open(os.path.join(DATA_DIR, '../scoring_rates.json'), 'r') as json_file:
    scoring_rates = json.load(json_file)
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, '../scoring_distribution.csv'), index_col=0)
TRIALS = 100000

df = pd.read_csv(os.path.join(DATA_DIR, 'season_2013_agg_final_processed_2022-07-21.csv'))
missing_courses = [
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 01 February  : Hull v Tottenham : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 08 February  : Aston Villa v West Ham : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 15 March     : Everton v Cardiff : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 15 March     : Southampton v Norwich : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 15 March     : Stoke v West Ham : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 22 March : Hull v West Brom : Match Odds',
    'Soccer : English Soccer : Barclays Premier League : Fixtures 22 March : Norwich v Sunderland : Match Odds',
    'Soccer : English Soccer : Barclays Premier League : Fixtures 29 March     : Swansea v Norwich : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 29 March     : West Brom v Cardiff : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 05 April     : Cardiff v C Palace : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 12 April : C Palace v Aston Villa : Match Odds',
    'Soccer : English Soccer : Barclays Premier League : Fixtures 12 April : Fulham v Norwich : Match Odds',
    'Soccer : English Soccer : Barclays Premier League : Fixtures 11 May : Cardiff v Chelsea : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 11 May : Liverpool v Newcastle : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 11 May : Man City v West Ham : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 11 May : Sunderland v Swansea : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 17 August : West Ham v Cardiff : Match Odds',
    'Soccer : English Soccer : Barclays Premier League : Fixtures 24 August    : Newcastle v West Ham : Match Odds',
    'Soccer : English Soccer : Barclays Premier League : Fixtures 15 September : Southampton v West Ham : Match Odds',
    # 'Soccer : English Soccer : Barclays Premier League : Fixtures 06 October   : Norwich v Chelsea : Match Odds',
]
missing_ids = df[df.Course.isin(missing_courses)]['Event ID'].unique()

team_df = df[['Event ID', 'selection_home', 'selection_away']].drop_duplicates().dropna()
team_df['Event ID'] = team_df['Event ID'].astype(int).astype(str)
teams = team_df.set_index('Event ID').T.to_dict()

for match_id, match_df in df[df['Event ID'].isin(missing_ids)].groupby('Event ID'):
    match_id = str(int(match_id))
    sim_file_h = os.path.join(SIM_DIR, f'{match_id}_home.csv')
    sim_file_a = os.path.join(SIM_DIR, f'{match_id}_away.csv')
    rates = scoring_rates.get(match_id, {'foo':0}).values()
    if not os.path.isfile(sim_file_h) or not os.path.isfile(sim_file_a) or not all(rates):
        logging.info(f'no file exists for {match_id}')
        if match_id in scoring_rates:
            home_team = teams[match_id]['selection_home']
            away_team = teams[match_id]['selection_away']
            match_rates = scoring_rates[match_id]
            scoring_rate_home = match_rates.get(home_team, 0)
            scoring_rate_home = scoring_rate_home if scoring_rate_home > 0 else np.mean([x[home_team] for x in list(scoring_rates.values()) if home_team in x])
            scoring_rate_away = match_rates.get(away_team, 0)
            scoring_rate_away = scoring_rate_away if scoring_rate_away > 0 else np.mean([x[away_team] for x in list(scoring_rates.values()) if away_team in x])
        else:
            scoring_rate_home = np.mean([x[home_team] for x in list(scoring_rates.values()) if home_team in x])
            scoring_rate_away = np.mean([x[away_team] for x in list(scoring_rates.values()) if away_team in x])

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

    sims_h = pd.read_csv(sim_file_h, index_col=0).drop(index=['score'])
    sims_a = pd.read_csv(sim_file_a, index_col=0).drop(index=['score'])
    sims_h.index = sims_h.index.astype(int)
    sims_a.index = sims_a.index.astype(int)

    match_df.sort_values('agg_key', inplace=True)
    home_goals = match_df.event_home.fillna('').apply(lambda x: len(re.findall('goal', x)))
    away_goals = match_df.event_away.fillna('').apply(lambda x: len(re.findall('goal', x)))
    df.loc[match_df.index, 'home_goal'] = home_goals
    df.loc[match_df.index, 'away_goal'] = away_goals
    home_own_goals = match_df.event_home.fillna('').apply(lambda x: len(re.findall('own goal', x))).cumsum()
    away_own_goals = match_df.event_away.fillna('').apply(lambda x: len(re.findall('own goal', x))).cumsum()
    home_scores = home_goals.cumsum() - home_own_goals + away_own_goals
    away_scores = away_goals.cumsum() - away_own_goals + home_own_goals
    df.loc[match_df.index, 'home_score'] = home_scores
    df.loc[match_df.index, 'away_score'] = away_scores
    start_index = match_df[match_df.event_home.fillna('').str.contains('start')].iloc[0].name
    half_index = match_df[match_df.event_home.fillna('').str.contains('start')].iloc[1].name

    first_half = True
    minute = 0
    for index, row in match_df.iterrows():
        if index == start_index-1:
            home_simulations = sims_h.sum()
            away_simulations = sims_a.sum()
            sim_home_w_prob = (home_simulations > away_simulations).sum() / home_simulations.shape[0]
            sim_away_w_prob = (home_simulations < away_simulations).sum() / home_simulations.shape[0]
            sim_draw_prob = (home_simulations == away_simulations).sum() / home_simulations.shape[0]
            df.loc[index, 'sim_prob_home'] = sim_home_w_prob
            df.loc[index, 'sim_prob_away'] = sim_away_w_prob
            df.loc[index, 'sim_prob_draw'] = sim_draw_prob
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
        df.loc[index, 'sim_prob_home'] = sim_home_w_prob
        df.loc[index, 'sim_prob_away'] = sim_away_w_prob
        df.loc[index, 'sim_prob_draw'] = sim_draw_prob

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
        home_score_home_sq_diff = math.pow((home_score_home_prob-row['prob_home']), 2)
        home_score_away_sq_diff = math.pow((home_score_away_prob-row['prob_away']), 2)
        home_score_draw_sq_diff = math.pow((home_score_draw_prob-row['prob_draw']), 2)
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
        away_score_home_sq_diff = math.pow((away_score_home_prob-row['prob_home']), 2)
        away_score_away_sq_diff = math.pow((away_score_away_prob-row['prob_away']), 2)
        away_score_draw_sq_diff = math.pow((away_score_draw_prob-row['prob_draw']), 2)
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

        df.loc[index, f'suspense'] = suspense
        df.loc[index, f'sim_suspense'] = sim_suspense
        df.loc[index, 'minute'] = minute

    new_match_df = df.loc[match_df.index]
    pre_match_probs = {}
    sim_cols = ['sim_prob_home', 'sim_prob_away', 'sim_prob_draw']
    for col in sim_cols:
        new_match_df[f'{col}-1'] = new_match_df[col].shift(1)
        pre_match_probs[col] = new_match_df.loc[start_index-1][col]

    sim_surprise = ((new_match_df['sim_prob_home'] - new_match_df['sim_prob_home-1']).apply(lambda x: pow(x, 2)) + \
                (new_match_df['sim_prob_away'] - new_match_df['sim_prob_away-1']).apply(lambda x: pow(x, 2)) + \
                (new_match_df['sim_prob_draw'] - new_match_df['sim_prob_draw-1']).apply(lambda x: pow(x, 2)))\
                .apply(lambda x: math.sqrt(x))

    sim_shock = ((new_match_df['sim_prob_home'] - pre_match_probs['sim_prob_home']).apply(lambda x: pow(x, 2)) + \
             (new_match_df['sim_prob_away'] - pre_match_probs['sim_prob_away']).apply(lambda x: pow(x, 2)) + \
             (new_match_df['sim_prob_draw'] - pre_match_probs['sim_prob_draw']).apply(lambda x: pow(x, 2)))\
             .apply(lambda x: math.sqrt(x))

    df.loc[match_df.index, 'sim_surprise'] = sim_surprise
    df.loc[match_df.index, 'sim_shock'] = sim_shock

df.loc[df.selection_home == 'Crystal Palace', 'selection_home'] = 'C Palace'
df.loc[df.selection_away == 'Crystal Palace', 'selection_away'] = 'C Palace'
df.loc[df['Event ID'] == 27136720, 'selection_home'] = 'Fulham'

minute = df.minute.notnull()
no_price = df.price_match_home.isnull() | df.price_match_away.isnull() | df.price_match_draw.isnull()
high_min = df.minute > 75
under_91 = df.minute < 91
mask = minute & no_price & high_min & under_91
missing_price_matches = df[mask]['Event ID'].unique() # 21 matches
for event_id, frame in df[df['Event ID'].isin(missing_price_matches)].groupby('Event ID'):
    cols = ['shock', 'surprise', 'suspense', 'price_match_home', 'price_match_away', 'price_match_draw', 'prob_draw', 'prob_away', 'prob_home']
    for col in cols:
        frame[col].ffill(inplace=True)

    df.loc[frame.index] = frame

trimmed_df = pd.DataFrame()
for event_id, frame in df.groupby('Event ID'):
    course = next(filter(lambda x: 'Second Half Match Odds' not in x, frame.Course.unique()))
    minute = frame.minute.count()
    shock = frame.shock.count()
    surprise = frame.surprise.count()
    suspense = frame.suspense.count()
    sim_shock = frame.sim_shock.count()
    sim_surprise = frame.sim_surprise.count()
    sim_suspense = frame.sim_suspense.count()
    if not all([minute, shock, surprise, suspense, sim_shock, sim_surprise, sim_suspense]):
        print(f'{course}\n{minute=} {shock=} {surprise=} {suspense=} {sim_shock=} {sim_surprise=} {sim_suspense=}\n')

    minute_df = frame.drop_duplicates('minute', keep='first')[['minute', 'shock', 'surprise', 'suspense', 'sim_shock', 'sim_surprise', 'sim_suspense', 'Course', 'selection_home']]
    minute_df = minute_df[minute_df.minute.notnull()]
    trimmed_df = pd.concat([minute_df.head(90), trimmed_df])

trimmed_df.groupby('selection_home').count()
(trimmed_df.groupby('selection_home').count() < 1710).any(axis=1)

# team_df = trimmed_df[trimmed_df.selection_home == 'Fulham']
# for x, y in team_df.groupby(['Course']):
#     if (y.count() < 90).any():
#         print(x)
#         print(y.isnull().sum())
#         break

df.to_csv(os.path.join(DATA_DIR, 'season_2013_agg_final_processed_2022-07-21.csv'), index=False)
