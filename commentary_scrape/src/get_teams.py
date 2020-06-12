import sys
import numpy as np
import pandas as pd
from glob import glob
import xml.dom.minidom
import xml.etree.ElementTree as et 

DATA_DIR = '/Users/philipramirez/commentary_scrape/data/'
TEXT_DIR = DATA_DIR + 'text/'

teamnames = {'C Palace' : 'Crystal Palace',
             'Man City' : 'Manchester City',
             'Man Utd' : 'Manchester United',
             'Newcastle' : 'Newcastle United',
             'QPR' : 'Queens Park Rangers',
             'West Brom' : 'West Bromwich Albion',
             'Wolves' : 'Wolverhampton Wanderers'}

teamnames_2 = {y : x for (x, y) in teamnames.items()}

folders = [DATA_DIR + x for x in ['season_2013_match_part1/', 'season_2013_match_part2/']]
for folder_name in folders:
    xml_files = glob(folder_name + '*')
    for xml_file in xml_files: 
        xtree = et.parse(xml_file)
        xroot = xtree.getroot()
        comment_df = pd.DataFrame([node.attrib for node in xroot]) 
        xml_attrib = xroot.attrib
        away_team = xml_attrib['away_team_name'].replace('2', '')
        franc_away = away_team if away_team not in teamnames_2 else teamnames_2[away_team]
        xml_attrib['away_team_name'] = franc_away
        home_team = xml_attrib['home_team_name'].replace('2', '')
        franc_home = home_team if home_team not in teamnames_2 else teamnames_2[home_team]
        xml_attrib['home_team_name'] = franc_home
        season = xml_attrib['season']
        season = season.split(' ')[-1].replace('/', '-')
        game_date = xml_attrib['game_date']
        game_date = game_date.split(' ')[0].replace('-', '')
        txt_file_pattern = '*{}-{}*_{}_{}.txt'.format(away_team, home_team, season, game_date)
        txt_files_found = glob(TEXT_DIR + txt_file_pattern)
        if len(txt_files_found) != 1:
            sys.exit('too many or not enough matches')

        txt_file = txt_files_found[0]
        txt_df = pd.read_csv(txt_file, encoding='utf-16', sep='\t')
        home_team_id = txt_df[txt_df['data-type'].isin([30,32])]['data-team-id'].iloc[-1]
        txt_df['team'] = np.where(txt_df['data-team-id'] == home_team_id, home_team, away_team)
        txt_df['team'] = txt_df['team'].apply(lambda x : x if x not in teamnames_2 else teamnames_2[x])
        merged_df = comment_df.join(txt_df['team'])

        commentary = et.Element('Commentary', xml_attrib)
        for index, row in merged_df.iterrows():
            message = et.SubElement(commentary, 'message')
            for attrib, value in row.iteritems():
                if pd.notnull(value):
                    message.set(attrib, value)

        xml_string = et.tostring(commentary, encoding='utf-16')
        outfile = open(xml_file, 'w')
        dom = xml.dom.minidom.parseString(xml_string)
        outfile.write(dom.toprettyxml())
        outfile.close()

