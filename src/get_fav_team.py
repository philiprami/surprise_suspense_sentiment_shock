import os
import gc
import sys
import json
import time
import ntpath
import statistics
import numpy as np
import pandas as pd
from glob import glob
from datetime import timedelta, datetime
import xml.etree.ElementTree as et

DATA_DIR = '../data/'
MASTER_DIR = DATA_DIR + 'Fracsoft/'
OUT_DIR = DATA_DIR + 'aggregated/'
COMMENTARY_DIR = DATA_DIR + 'commentaries/'
SENTIMENT_DIR = DATA_DIR + 'Sentiment Scores/'

with open(DATA_DIR + 'cols.json','r') as column_file:
    cols = json.load(column_file)

with open(DATA_DIR + 'sentiment_map.json', 'r') as json_file:
    file_map = json.load(json_file)
    for x, y in list(file_map.items()):
        file_map[x.replace('_merged', '')] = file_map[x]
    for key in list(file_map.keys()):
        for event_num in file_map[key]:
             file_map[event_num] = file_map[key][event_num]

team_names = \
{'Crystal Palace': 'C Palace',
 'Manchester City': 'Man City',
 'Manchester United': 'Man Utd',
 'Newcastle United': 'Newcastle',
 'Newcastle':'Newcastle United',
 'Queens Park Rangers': 'QPR',
 'West Bromwich Albion': 'West Brom',
 'Wolverhampton Wanderers': 'Wolves'}

sentiment_frame = pd.DataFrame()
scores_frame = pd.DataFrame()
master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*.csv*'))
for master_file in master_files:
    master_dir, master = ntpath.split(master_file)
    df = pd.read_csv(master_file, header=None)
    df.columns = [str(x) for x in df.columns]
    df.rename(columns=cols, inplace=True)
    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['Date'] + 'T' + df['Time stamp']).dt.round('s')
    else:
        df['datetime'] = pd.to_datetime(df['datetime'])

    df = df[~df['selection'].str.contains('Over |Under ')].reset_index(drop=True)
    df = df[~df['selection'].str.contains('/', regex=False)].reset_index(drop=True)
    df = df[df['selection'] != 'Draw'].reset_index(drop=True)
    gb = df.groupby(['Event ID', 'selection'])
    for (match_id, selection), match_df in gb:
        print(match_id)

        # merge in twitter numbers
        if str(match_id) not in file_map:
            print('missing match twitter data: ', match_df.iloc[0]['Course'])
            continue

        match_files = file_map[str(match_id)]
        selection_files = [x for x in match_files if selection in x]
        if selection == 'The Draw':
            continue

        if len(selection_files) != 1:
            print('missing selection: ', selection)
            print(match_files)
            continue

        match_file = selection_files[0]
        if match_file == 'epl-Crystal Palace-2013-08-18.csv':
            print('crystal palce. continue')
            continue

        match_df.sort_values('datetime', inplace=True)
        game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
        game_start_mask = (match_df['Inplay flag'] == 1) & (match_df['datetime'] >= game_start)
        if game_start_mask.sum() < 1:
            print(match_df.iloc[0].Course)
            continue

        actual_start = match_df[game_start_mask].sort_values('datetime').iloc[0]['datetime']
        game_end = match_df.iloc[-1].datetime
        sent_df = pd.read_csv(SENTIMENT_DIR + match_file)
        sent_df['time'] = pd.to_datetime(sent_df['time'])
        sent_df['time'] = sent_df['time'].apply(lambda x: x.replace(tzinfo=None))
        sent_df.sort_values('time', inplace=True)
        game_start = pd.to_datetime(f'{match_df.Date.all()} {match_df.time.all()}')
        twitter_actual_start = game_start - timedelta(hours=1)
        offset = twitter_actual_start - min(sent_df.time)
        sent_df['time'] = sent_df['time'] + offset
        after_game = sent_df['time'] >= game_end
        av_pred = sent_df[after_game].groupby('tweeter_name')['predictions'].mean()
        av_pred.name = f'{match_id}-{selection}'
        sentiment_frame = sentiment_frame.join(av_pred, how='outer')

        xml_name = ';'.join(match_df['Course'].iloc[0].split(':')[:-1]).strip() + '.xml'
        xml_file = COMMENTARY_DIR + master.replace('.csv.gz', '/').replace('.csv', '/') + xml_name
        if not os.path.isfile(xml_file):
            print('missing ', xml_name)
            continue

        xtree = et.parse(xml_file)
        xroot = xtree.getroot()
        comment_df = pd.DataFrame([node.attrib for node in xroot])
        comment_df.second = comment_df.second.fillna(0)
        comment_df.minute = comment_df.minute.astype(int)
        second_half_index = comment_df[comment_df['comment'] == 'Second half begins!'].iloc[0].name
        second_half = comment_df[comment_df.index <= second_half_index]
        second_half.iloc[0]['last_modified'] = game_end
        game_end_seconds = int(second_half.iloc[0]['second']) + int(second_half.iloc[0]['minute']) * 60
        second_half['last_modified'] = second_half[['minute', 'second']].\
          apply(lambda x: game_end - timedelta(seconds=(game_end_seconds - (int(x[1]) + int(x[0]) * 60))), axis=1)
        first_half = comment_df[comment_df.index > second_half_index]
        first_half['last_modified'] = first_half[['minute', 'second']].\
          apply(lambda x: actual_start + timedelta(minutes=int(x[0]), seconds=int(x[1])), axis=1)
        second_half.loc[second_half['minute'] > 90, 'minute'] = 90
        first_half.loc[first_half['minute'] > 45, 'minute'] = 45
        comment_df = pd.concat([second_half, first_half])
        comment_df.sort_values('last_modified', inplace=True)
        comment_df['goal_scored'] = np.where(comment_df.type == 'goal scored', 1, 0)
        reverse_dict = {xroot.attrib['home_team_name'].replace('2', '') : xroot.attrib['away_team_name'].replace('2', ''),
                        xroot.attrib['away_team_name'].replace('2', '') : xroot.attrib['home_team_name'].replace('2', '')}
        teams = list(reverse_dict.keys())
        try:
            selection_df = comment_df[comment_df['team'] == reverse_dict[selection]]
            teams.remove(selection)
        except KeyError:
            selection_df = comment_df[comment_df['team'] == reverse_dict[team_names[selection]]]
            teams.remove(team_names[selection])

        other_team = teams[0]
        try:
            other_df = comment_df[comment_df['team'] == reverse_dict[other_team]]
        except KeyError:
            other_df = comment_df[comment_df['team'] == reverse_dict[team_names[other_team]]]

        selection_score = selection_df['goal_scored'].sum()
        other_score = other_df['goal_scored'].sum()
        if selection_score == other_score:
            score_line = 0
        elif selection_score < other_score:
            score_line = -1
        else:
            score_line = 1

        scores_frame.loc[0, f'{match_id}-{selection}'] = score_line

mult_df = sentiment_frame.copy()
for col in sentiment_frame.columns:
    mult_df[col] = scores_frame[col].iloc[0]

sent_polarized = sentiment_frame * mult_df
sent_polarized.columns = [x.split('-')[1] for x in sent_polarized.columns]
results = []
for tweeter, row in sent_polarized.iterrows():
    sorted_row = row.sort_values(ascending=False)
    max_score_team = sorted_row.index[0]
    try:
        top_team = statistics.mode(sorted_row[sorted_row > 0].dropna()[:5].index)
    except:
        results.append([tweeter, None])
        continue

    if max_score_team != top_team:
        results.append([tweeter, None])
    else:
        results.append([tweeter, sorted_row.index[0]])

final = pd.DataFrame(results, columns=['twitter_name', 'fav_team'])
final.to_csv(DATA_DIR + 'favorite_teams.csv', index=False)

# minimum amount of tweets?
# instead of taking the top answer, consider taking the mode of the top 3 or top 5
