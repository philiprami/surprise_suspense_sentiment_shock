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
-   Account for red cards by modifying scoring rates

'''

import os
import pandas as pd
import xml.etree.ElementTree as et

from glob import glob
from scipy.stats import poisson

DATA_DIR = '../data/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
price_cols = ['eff_price_match', 'mean_price_match', 'median_price_match']
prob_cols = ['eff_prob', 'mean_prob', 'median_prob']
outcomes = ['home', 'away', 'draw']

INPUT = pd.read_csv(OUT_DIR + 'season_2013_agg_scaled_0502.csv')
OUTPUT = pd.DataFrame()

all_score_line_probs = {}
event_gb = INPUT.groupby('Event ID')
minute_goals = {}
num_matches = 0
for match_id, match_df in event_gb:
    print(match_id)
    # get event file
    xml_name = ';'.join(match_df['Course'].iloc[0].split(':')[:-1]).strip() + '.xml'
    xml_file = None
    for folder in os.listdir(COMMENTARY_DIR):
        if os.path.isdir(os.path.join(COMMENTARY_DIR, folder)):
            for filename in os.listdir(os.path.join(COMMENTARY_DIR, folder)):
                if filename == xml_name:
                    xml_file = os.path.join(COMMENTARY_DIR, folder, filename)
                    break

    if not os.path.isfile(xml_file):
        print('missing ', xml_name)
        continue


    xtree = et.parse(xml_file)
    xroot = xtree.getroot()
    comment_df = pd.DataFrame([node.attrib for node in xroot])

    comment_df.second = comment_df.second.fillna(0)
    second_half_index = comment_df[comment_df['comment'] == 'Second half begins!'].iloc[0].name
    second_half = comment_df[comment_df.index <= second_half_index]
    second_half.iloc[0]['last_modified'] = game_end
    game_end_seconds = int(second_half.iloc[0]['second']) + int(second_half.iloc[0]['minute']) * 60
    second_half['last_modified'] = second_half[['minute', 'second']].\
      apply(lambda x: game_end - timedelta(seconds=(game_end_seconds - (int(x[1]) + int(x[0]) * 60))), axis=1)
    first_half = comment_df[comment_df.index > second_half_index]
    first_half['last_modified'] = first_half[['minute', 'second']].\
      apply(lambda x: actual_start + timedelta(minutes=int(x[0]), seconds=int(x[1])), axis=1)
    comment_df = pd.concat([second_half, first_half])
    
    comment_df.sort_values(['minute', 'second'], inplace=True)
    home_goal = (comment_df.team == match_df.selection_home.all()) & (comment_df.type == 'goal scored')
    away_goal = (comment_df.team == match_df.selection_away.all()) & (comment_df.type == 'goal scored')
    comment_df.loc[home_goal, 'home_goal'] = 1
    comment_df.loc[away_goal, 'away_goal'] = 1
    comment_df.fillna(0, inplace=True)
    comment_df['home_score'] = comment_df['home_goal'].cumsum()
    comment_df['away_score'] = comment_df['away_goal'].cumsum()

    comment_df['minute'] = comment_df['minute'].astype(int) + 1
    comment_df.loc[comment_df['minute'] > 90, 'minute'] = 90


    end_home_score = comment_df.iloc[-1]['home_score']
    end_away_score = comment_df.iloc[-1]['away_score']
    poisson_home = poisson(end_home_score)
    poisson_away = poisson(end_away_score)
    # outcome_prob = poisson_home.pmf(end_home_score) + poisson_away.pmf(end_away_score)
    # scoring_rate_home = # minimize squared diff
    comment_df['score_line'] = comment_df[['home_score', 'away_score']].apply(lambda x: f'{int(x[0])}-{int(x[1])}', axis=1)
    score_lines = comment_df.score_line.unique()
    score_line_probs = {}
    for score_line in score_lines:
        home_score, away_score = score_line.split('-')
        prob = poisson_home.pdf(int(home_score)) + poisson_away.pdf(int(away_score))
        score_line_probs[score_line] = prob

    match_df.sort_values('agg_key', inplace=True)
    closing_line = match_df[match_df['Inplay flag'] == 0].iloc[-1]



    def estimate_lambda(score, lmbda):
        poi_dis = poisson(lmbda)
        return poi_dis.pmf(score)

    # part 2... given scoring rates







    comment_df['score_line'] = comment_df[['home_score', 'away_score']].apply(lambda x: f'{int(x[0])}-{int(x[1])}', axis=1)
    score_lines = comment_df.score_line.unique()

    comment_df['home_prob'] = comment_df['home_score'].apply(lambda x: poisson_home.pmf(x))
    comment_df['away_prob'] = comment_df['away_score'].apply(lambda x: poisson_away.pmf(x))
    comment_df['score_line_prob'] = comment_df['home_prob'] * comment_df['away_prob']
    score_line_probs = {}
    for score_line in score_lines:
        home_score, away_score = score_line.split('-')
        prob = poisson_home.pdf(int(home_score)) + poisson_away.pdf(int(away_score))
        score_line_probs[score_line] = prob



    # join comment df and agg event_df
    comment_df.rename(columns={'last_modified' : 'agg_key'}, inplace=True)
    merged = match_df.merge(comment_df, on='agg_key', how='left')



    score_line_probs = {}
    for away_score in range(int(end_away_score)+1):
        away_prob = poisson_away.pmf(away_score)
        for home_score in range(int(end_home_score)+1):
            home_prob = poisson_home.pmf(home_score)
            score_line = f'{home_score}-{away_score}'
            score_line_probs[score_line] = home_prob + away_prob

    all_score_line_probs[str(int(match_id))] = score_line_probs



    goal_counts = comment_df[comment_df.type == 'goal scored'].groupby('team').agg('count').type
    home_goals = goal_counts[match_df.selection_home.all()]
    away_goals = goal_counts[match_df.selection_away.all()]
    comment_df.sort_values('last_modified')

    break

    # run simulations
    import simpy
    import random
    import statistics
