import os
import re
import pandas as pd
from glob import glob
from datetime import timedelta
import xml.etree.ElementTree as ET

DATA_DIR = '/Users/philipramirez/Downloads/'
DATA_FILES = glob(DATA_DIR + '*.csv')
XML_DIR = '../data/xml/'
XML_FILES = glob(XML_DIR + '*')
XML_OUTDIR = '../data/xml_timed/'
OUTFILES = glob(XML_OUTDIR + '*')

teamnames = {'C Palace' : 'Crystal Palace',
             'Man City' : 'Manchester City',
             'Man Utd' : 'Manchester United',
             'Newcastle' : 'Newcastle United',
             'QPR' : 'Queens Park Rangers',
             'West Brom' : 'West Bromwich Albion',
             'Wolves' : 'Wolverhampton Wanderers'}

total_teams = set() # keeping track of team names

for csv_file in DATA_FILES:
    season_pattern = 'season_([0-9]+)_'
    season_1 = int(re.search(season_pattern, csv_file).groups()[0])
    if season_1 != 2012:
        continue
    season_2 = season_1 + 1
    season = '{}-{}'.format(season_1, season_2)
    df_iter = pd.read_csv(csv_file, header=None, chunksize=100000)
    for df in df_iter:
        unique_matches = df[3].unique()
        for match in unique_matches:
            filenames.add((row[3].split(':')[-2].strip(), row[3].split(':')[-3].strip()))
            match_mask = df[3] == match
            mask = match_mask & (df[7] == 1)
            if mask.sum():
                row = df[match_mask & df[7] == 1].iloc[0]
                matchups = row[3].split(':')[-2].strip().split(' v ')
                for i, team in enumerate(matchups):
                    total_teams.add(team)
                    if team in teamnames:
                        matchups[i] = teamnames[team]

                matchup = '-'.join(matchups)
                date = row[0].replace('-', '')
                filename = '{}_{}_{}.xml'.format(matchup, season, date)
                game_time_str = row[0] + ' ' + row[1]
                actual_start_str = row[0] + ' ' + row[6]
                actual_start = pd.to_datetime(actual_start_str).replace(microsecond=0)
                if XML_DIR + filename not in XML_FILES:
                    print(filename)
                    continue
                elif XML_OUTDIR + filename in OUTFILES:
                    print('skipping ' + filename)
                else:
                    tree = ET.parse(XML_DIR + filename)
                    root = tree.getroot()
                    root.attrib['game_id_2'] = str(row[2])
                    root.attrib['game_id_4'] = str(row[4])
                    root.attrib['game_date'] = game_time_str
                    for child in root:
                        secs = int(child.attrib['second']) if 'second' in child.attrib else 0
                        mins = int(child.attrib['minute'])
                        mod_time = actual_start + timedelta(seconds=secs, minutes=mins)
                        child.attrib['last_modified'] = mod_time.isoformat().replace('T', ' ')

                    xml_string = ET.tostring(root, encoding='utf-16')
                    outfilename = XML_OUTDIR + filename
                    tree.write(outfilename, encoding='utf-16')
