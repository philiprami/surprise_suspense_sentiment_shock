'''
step 3 of calculating suspense
'''

import os
import sys
import time
import json
import subprocess
from queue import Queue
from threading import Thread

DATA_DIR = '../data/'
with open(os.path.join(DATA_DIR, 'scoring_rates.json'), 'r') as json_file:
    scoring_rates = json.load(json_file)

q = Queue()
for match_id in scoring_rates:
    q.put(match_id)
q.put(None)

def sub_stuff(match):
    print(f'runnning thread for match {match}')
    terminalCommand = "python simulate_goals_solo.py -m " + match
    subprocess.run(terminalCommand, shell=True)

def worker():
    while True:
        match = q.get()
        if match is None:
          return

        sub_stuff(match)

num_workers = 10
threads = [Thread(target=worker) for _i in range(num_workers)]
for thread in threads:
    thread.start()
