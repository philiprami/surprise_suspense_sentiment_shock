import requests
import pandas as pd

df = pd.DataFrame()
years = range(2010, 2015)
months = range(1, 13)
for year in reversed(years):
    print 'getting year {}'.format(year)
    for month in months:
        month = str(month)
        while len(month) < 2:
            month = '0' + month

        end_date = '{}-{}-31'.format(year, month)
        start_date = '{}-{}-01'.format(year, month)
        endpoint = '''
        https://push.api.bbci.co.uk/b?t=%2Fdata%2Fbbc-morph-football-scores-match-list-data%2FendDate%2F{}%2FstartDate%2F{}%2FtodayDate%2F2020-01-28%2Ftournament%2Fpremier-league%2Fversion%2F2.4.1?timeout=5
        '''.format(end_date, start_date)#.format('2018-01-31', '2018-01-01')
        response = requests.get(endpoint)
        data = response.json()
        payload = data['payload'][0]
        match_data = payload['body']['matchData']
        if len(match_data):
            match_dates = match_data[0]['tournamentDatesWithEvents']
            for tourny_date in match_dates:
                events = match_dates[tourny_date][0]['events']
                for event in events:
                    away_team = event['awayTeam']['name']['full']
                    home_team = event['homeTeam']['name']['full']
                    start_time = event['startTime']
                    game_id = event['cpsId']
                    href = 'https://www.bbc.com' + event['href'] if event['href'] else None
                    row = {'away_team' : away_team,
                           'home_team' : home_team,
                           'start_time' : start_time,
                           'game_id' : game_id,
                           'href' : href}

                    df = df.append(row, ignore_index=True)

df.to_csv('../data/game_links.csv', index=False)
