'''
One time script to rename files
'''

import os
import shutil
import ntpath
from glob import glob
import pandas as pd
import xml.etree.ElementTree as ET

XML_DIR = '/Users/philipramirez/commentary_scrape/data/xml_timed/'
XML_FILES = glob(XML_DIR + '*')
DATA_DIR = '/Users/philipramirez/Downloads/'
DATA_FILES = glob(DATA_DIR + '*.csv')
OUT_DIR = '/Users/philipramirez/commentary_scrape/data/'

match_csv_data = {}
for csv_file in DATA_FILES:
    df_iter = pd.read_csv(csv_file, header=None, chunksize=100000)
    for df in df_iter:
        unique_matches = df[3].unique()
        for match in unique_matches:
            match_mask = df[3] == match
            row = df[match_mask].iloc[0]
            match_csv_data[str(row[2])] = {'match' : match, 'filename' : csv_file}

for xml_file in XML_FILES:
    tree = ET.parse(xml_file)
    root = tree.getroot()
    if 'game_id_2' not in root.attrib:
        print(root)
        continue
        
    key = root.attrib['game_id_2']
    value = match_csv_data[key]
    out = OUT_DIR + ntpath.split(value['filename'])[1].replace('.csv', '/')
    if not os.path.isdir(out):
        os.makedirs(out)

    filename = ':'.join(value['match'].split(':')[:-1]).strip() +'.xml'
    shutil.os.rename(xml_file, out + filename)
