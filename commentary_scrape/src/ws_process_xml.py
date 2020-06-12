import ntpath
import pandas as pd
from glob import glob
from datetime import datetime
import xml.dom.minidom
import xml.etree.ElementTree as ET

TEXT_DIR = '../data/text/'
TEXT_FILES = glob(TEXT_DIR + '*')

dtypes_dict = {6 : 'corner',
               10 : 'save made',
               13 : 'attempt missed',
               14 : 'woodwork hit',
               15 : 'attempt blocked',
               16 : 'goal scored',
               17 : 'card received',
               18 : 'substitution off',
               19 : 'substitution on',
               30 : 'end',
               32 :'start',
               10000 : 'offside'}

for t_file in TEXT_FILES:
    tdir, filename = ntpath.split(t_file)
    matchup, season, game_date = filename.split('_')
    season_id = season.split('-')[0]
    season_str = 'Season {}'.format(season.replace('-', '/'))
    game_date = game_date.replace('.txt', '')
    date_str = datetime.strptime(game_date, '%Y%m%d').strftime('%Y-%m-%d')
    away_team, home_team = [x.replace('1', '').replace('2', '') for x in matchup.split('-')]
    comm_attrs = {'away_team_name' : away_team,
                  'home_team_name' :home_team,
                  'season' : season_str,
                  'season_id' : season_id,
                  'game_date' : date_str,
                  'competition' : 'English Premier League',
                  'sport_id' : '1',
                  'sport_name' : 'Football',
                  'lang_id' : 'en'}

    commentary = ET.Element('Commentary', comm_attrs)
    df = pd.read_csv(t_file, encoding='utf-16', sep='\t')
    for index, row in df.iterrows():
        message = ET.SubElement(commentary, 'message')
        message.set('comment', row['comment'].strip())
        message.set('period', str(row['data-period-id']))
        message.set('minute', str(row['data-minute']))
        if not pd.isnull(row['data-second']):
            message.set('second', str(int(row['data-second'])))
        message.set('time', str(row['data-expanded-minute']))
        message.set('type', dtypes_dict[row['data-type']])
        message.set('type_id', str(row['data-type']))

    xml_string = ET.tostring(commentary, encoding='utf-16')
    outfilename = tdir.replace('text', 'xml') + \
      '/{}-{}_{}_{}.xml'.format(away_team, home_team, season, game_date)
    outfile = open(outfilename, 'w')
    dom = xml.dom.minidom.parseString(xml_string)
    outfile.write(dom.toprettyxml())
    outfile.close()
