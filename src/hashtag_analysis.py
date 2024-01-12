import os
import json
import pandas as pd

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
SENTIMENT_DIR = os.path.join(DATA_DIR, 'Sentiment Scores')
DATASET_PATH = os.path.join(OUT_DIR, 'season_2013_agg_final_processed_2022-07-21.csv')

fan_data = pd.read_csv(os.path.join(DATA_DIR, 'favorite_teams.csv'))
with open(os.path.join(DATA_DIR, 'sentiment_map.json'), 'r') as json_file:
    file_map = json.load(json_file)
    for x, y in list(file_map.items()):
        file_map[x.replace('_merged', '')] = file_map[x]
    for key in list(file_map.keys()):
        for event_num in file_map[key]:
             file_map[event_num] = file_map[key][event_num]

df = pd.read_csv(DATASET_PATH)
result = pd.DataFrame()
for match_id, match_df in df.groupby('Event ID'):
    # selections = [x for x in match_df['selection'].unique() if x != "The Draw"]
    selections = [match_df['selection_home'].unique()[0], match_df['selection_away'].unique()[0] ]
    for selection in selections:
        if str(int(match_id)) not in file_map:
            print('missing match twitter data: ', match_df.iloc[0]['Course'])
            continue

        match_files = file_map[str(int(match_id))]
        selection_files = [x for x in match_files if selection in x]
        if len(selection_files) != 1:
            print('missing selection: ', selection)
            print(selection_files)
            continue

        match_file = selection_files[0]
        if match_file == 'epl-Crystal Palace-2013-08-18.csv':
            continue

        selection_df = pd.read_csv(os.path.join(SENTIMENT_DIR, match_file))
        fans = fan_data[fan_data.fav_team == selection]
        opp = next(filter(lambda x: x != selection, selections))
        opp_file = next(filter(lambda x: x != match_file, match_files))
        opp_df = pd.read_csv(os.path.join(SENTIMENT_DIR, opp_file))
        fans_on_opp = opp_df.tweeter_name.isin(fans.twitter_name)
        with_opp_hastag = selection_df.tweet.str.lower().str.contains(f"#{opp.lower().replace(' ', '')}")
        record = {
                    "event_id": match_id,
                    "selection": selection,
                    "opponent": opp,
                    "num_tweets_total": selection_df.shape[0],
                    "num_opponent_hashtags": with_opp_hastag.sum(),
                    "num_fans_w_opp_hastags": fans_on_opp.sum()
        }
        result = result.append(record, ignore_index=True)
        # sys.exit()

# result.to_csv('hashtag_analysis_v0.csv', index=False)
