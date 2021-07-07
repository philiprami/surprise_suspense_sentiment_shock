'''
1) Score lines per match
-   Objective: estimate the scoring rates of each team
-   Ingredients:
        o    Closing odds on the result averaged over bookmakers
        o    Closing odds on O/U-totals averaged over bookmakers
-   Procedure:
        o    Assuming independently Poisson distributed number of goals scored b H and A
        o    Predict the scoreline probabilities for each match (match-level)
        o    Sum all predicted scoreline probabilities to calculate the probabilities of potential match outcomes
        o    Estimate scoring rates by minimizing the squared difference between the bookmaker implied probabilities
             and the outcome probabilities from the in-play model
2) Score lines per minute
-    Objective: distributing scoring rates across the minutes
-    Ingredients: use scores dataset
-    Procedure:
        o    Assume the average amount of injury time to evenly share out the inflated scoring rates in the
             45th and 90th min across these extra minutes
        o    Presume all matches to be 93 min long
        o    Calculate a moving average over 15 min to smooth the relative frequency distributions
        o    Backward interpolate the missing values at the beginning of each series (first 15 min)
        o    calculate the density function of goals scored per minute
-   Problem:
        o    average scoring behavior might not adequately represent a team’s scoring pattern
        o    eventually use team-specific empirical goal distributions (though then we might have several zeros since not all teams score in all minutes)
3) Number of goals per minute
-   Simulate the number of goals in each minute using the score lines per minute
-   Sum up score line and record result, repeat 100,000 times per min => 9 Mio times per match
4) Calculate hypothetical probabilities
-   what are the probabilities for H-win, draw, A-win if either H or A do score in the next min
-   to calculate suspense
    - iterate through each minute
        - get the probabilities for H-win, draw and A-win given a home score (use simulation values added to current home score)
            - square the difference between these and the given probabilities for H-win, draw and A-win for the minute
            - multiply that squared differene by the probability of scoring in the next minute
            - sum all of these values
        - get the probabilities for H-win, draw and A-win given an away score (use simulation values added to current away score)
            - square the difference between these and the given probabilities for H-win, draw and A-win for the minute
            - multiply that squared differene by the probability of scoring in the next minute
            - sum all of these values
        - sum the sum of values
-   Account for red cards by modifying scoring rates

'''

import os
import gc
import re
import math
import pandas as pd

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
DATA_DF = pd.read_csv(os.path.join(OUT_DIR, 'season_2013_agg_final_0706.csv'))

done = set()
for match_id, match_df in DATA_DF.groupby('Event ID'):
    match_id = str(int(match_id))
    if match_id in done:
        print(f'{match_id} already done. skipping.')
        continue

    sim_file_h = os.path.join(SIM_DIR, f'{match_id}_home.csv')
    sim_file_a = os.path.join(SIM_DIR, f'{match_id}_away.csv')
    if not os.path.isfile(sim_file_h) or not os.path.isfile(sim_file_a):
        print(f'no file exists for {match_id}')
        continue

    print(f'running for {match_id}')
    sims_h = pd.read_csv(sim_file_h, index_col=0).drop(index=['score'])
    sims_a = pd.read_csv(sim_file_a, index_col=0).drop(index=['score'])
    sims_h.index = sims_h.index.astype(int)
    sims_a.index = sims_a.index.astype(int)
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
            DATA_DF.loc[index, f'suspense_{col}_prob'] = suspense #change

        minute += 1
        del minute_score_home
        del minute_score_away
        del home_simulations
        del away_simulations
        gc.collect()

    done.add(match_id)
    del match_df
    del sims_h
    del sims_a
    gc.collect()

DATA_DF.to_csv(os.path.join(OUT_DIR, 'season_2013_complete_0706.csv'), index=False)
