import os
import gc
import sys
import json
import time
import shutil
import ntpath
import numpy as np
import pandas as pd
from glob import glob
from datetime import timedelta
import xml.dom.minidom
import xml.etree.ElementTree as et

DATA_DIR = '/Volumes/My Passport/'
MASTER_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Fracsoft betting data/'
COMMENTARY_DIR = DATA_DIR + 'Box. Surprise, suspense and sentiment from twitter/Match commentaries/'
changed_files = set()
missing_files = set()

master_files = sorted(glob(MASTER_DIR + '*season_2013_match_part*_merged.csv.gz'))
for master_file in master_files:
    master_dir, master = ntpath.split(master_file)
    df = pd.read_csv(master_file)
    df.columns = [str(x) for x in df.columns]
    if 'datetime' not in df.columns:
        df['datetime'] = pd.to_datetime(df['0'] + 'T' +df['6']).dt.round('s')
    else:
        df['datetime'] = pd.to_datetime(df['datetime'])

    gb = df.groupby('2')
    for match_id, match_df in gb:
        match_df.sort_values('datetime', inplace=True)
        game_start = match_df[match_df['7'] == 1].iloc[0]['datetime']
        xml_name = ';'.join(match_df['3'].iloc[0].split(':')[:-1]).strip() + '.xml'
        xml_file = COMMENTARY_DIR + master.replace('_merged.csv.gz', '/') + xml_name
        if not os.path.isfile(xml_file):
            print(xml_name)
            missing_files.add(xml_name)
            continue

        print('reading match file: ' + xml_name)
        xtree = et.parse(xml_file)
        xroot = xtree.getroot()
        comment_df = pd.DataFrame([node.attrib for node in xroot])
        
        # get times
        comment_df.second = comment_df.second.fillna(0)
        comment_df['last_modified'] = \
          comment_df[['minute', 'second']].apply(lambda x: game_start + timedelta(minutes=int(x[0]), seconds=int(x[1])),
                                                 axis=1)

        # get card info
        card_mask = comment_df['type_id'] == '17'
        red_cards = card_mask & comment_df['comment'].str.contains('red', case=False)
        yellow_cards = card_mask & comment_df['comment'].str.contains('yellow', case=False)
        comment_df.loc[yellow_cards, 'type'] = 'yellow card'
        comment_df.loc[yellow_cards, 'type_id'] = '20'
        comment_df.loc[red_cards, 'type'] = 'red card'
        comment_df.loc[red_cards, 'type_id'] = '21'

        commentary = et.Element('Commentary', xroot.attrib)
        for index, row in comment_df.iterrows():
            message = et.SubElement(commentary, 'message')
            for attrib, value in row.iteritems():
                message.set(attrib, str(value))

        xml_string = et.tostring(commentary, encoding='utf-16')
        outfilename = xml_file.replace('/Match commentaries/', '/Match commentaries copy/')
        direct = ntpath.split(outfilename)[0]
        if not os.path.isdir(direct):
            shutil.os.makedirs(direct)
        outfile = open(outfilename, 'w')
        dom = xml.dom.minidom.parseString(xml_string)
        outfile.write(dom.toprettyxml())
        outfile.close()
        changed_files.add(xml_file)
