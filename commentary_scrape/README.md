# commentary_scrape

API LINK EX:
https://push.api.bbci.co.uk/b?t=%2Fdata%2Fbbc-morph-football-scores-match-list-data%2FendDate%2F2019-01-31%2FstartDate%2F2019-01-01%2FtodayDate%2F2020-01-28%2Ftournament%2Fpremier-league%2Fversion%2F2.4.1?timeout=5

Seasons:
premier league
2011-12, 2012-13 and 2013-14

ESPN
ex link:
https://www.espn.com/soccer/ ->
https://www.espn.com/soccer/scoreboard?league=eng.1 ->
https://www.espn.com/soccer/commentary?gameId=345542

api link
https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard?lang=en&region=us&calendartype=whitelist&limit=100&showAirings=true&dates=20110814&tz=America%2FNew_York&league=eng.1

whoscored
https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/2935/England-Premier-League
https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/3389/England-Premier-League
https://www.whoscored.com/Regions/252/Tournaments/2/Seasons/3853/England-Premier-League
->

https://www.whoscored.com/Matches/507272/MatchReport/England-Premier-League-2011-2012-Blackburn-Wigan
->
https://www.whoscored.com/Matches/507272/Live/England-Premier-League-2011-2012-Blackburn-Wigan

OPTA:
http://praxis.optasports.com/documentation/football-feed-specifications/f13-commentary-feed.aspx
optaclient
b@llond0r

Missing fields:
away_score, away_team_id, competition_id, game_id, home_score,
home_team_id, matchday, comment-id, player_ref1

Different fields:
game_date ... only the date is included
