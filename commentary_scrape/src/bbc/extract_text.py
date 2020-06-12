import requests
import pandas as pd
from bs4 import BeautifulSoup

df = pd.read_csv('../data/game_links.csv')
df = df[df.game_id.notnull()]

for index, row in df.iterrows():
    game_link = row['href']
    response = requests.get(game_link)
    data = response.text
    soup = BeautifulSoup(response.text, 'lxml')
