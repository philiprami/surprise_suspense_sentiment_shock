import csv
import gc
import os
import time
from datetime import datetime
from glob import glob

import pandas as pd
from transformers import pipeline


DATA_DIR = '../data/'
SENT_DIR = os.path.join(DATA_DIR, 'Sentiment Scores')
SENT_OUT_DIR = os.path.join(SENT_DIR, str(datetime.now().date()))
SENT_FILES = glob(os.path.join(SENT_DIR, '*.csv'))


model = pipeline(model="finiteautomata/bertweet-base-sentiment-analysis")
processed_files = set(glob(os.path.join(SENT_OUT_DIR, '*.csv')))
os.makedirs(SENT_OUT_DIR, exist_ok=True)
for filename in SENT_FILES:
    if filename in processed_files:
        continue

    start = time.time()
    df = pd.read_csv(filename)
    records = []
    for i, row in df.iterrows():
        record = row.to_dict()
        predictions = model(row.tweet[:120])
        if len(predictions):
            pred = predictions[0]
            record['label'] = pred.get('label')
            record['score'] = pred.get('score')
            records.append(record)

    out = os.path.join(SENT_OUT_DIR, os.path.basename(filename))
    pd.DataFrame(records).to_csv(out, index=False, quoting=csv.QUOTE_ALL)
    processed_files.add(filename)
    end = time.time()
    print(f"Processing time: {end-start} seconds. {df.shape[0]} records")
    del df
    gc.collect()
