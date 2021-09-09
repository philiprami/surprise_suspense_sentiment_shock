import os
import pickle
import pandas as pd
from glob import glob
from nlp import remove_noise
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize


DATA_DIR = '../data/'
SENT_DIR = os.path.join(DATA_DIR, 'Sentiment Scores')
SENT_FILES = glob(os.path.join(SENT_DIR, '*'))
MASTER_DIR = os.path.join(DATA_DIR, 'stanfordSentimentTreebankRaw')

with open(os.path.join(MASTER_DIR, 'random_forest_2021-09-02_16-45-59.p'), 'rb') as infile:
    rf_model = pickle.load(infile)

# figure out how to unpickle vectorizer

processed_files = set()
for filename in SENT_FILES:
    if filename in processed_files:
        print(f'skipping processed file: {filename}')
        continue
    try:
        df = pd.read_csv(filename)
        processed = [remove_noise(word_tokenize(tokens), stop_words) for tokens in df.tweet]
        vectorized = tdif_vectorizer.transform(processed)
        predictions = rf_model.predict(vectorized)
        df['predictions'] = predictions
        df.to_csv(filename, index=False, quoting=csv.QUOTE_ALL)
        processed_files.add(filename)
    except:
        print(f'cannot process file: {filename}')
