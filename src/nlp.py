import os
import re
import csv
import json
import string
import pickle
import numpy as np
import pandas as pd
from glob import glob
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer


DATA_DIR = '../data/'
SENT_DIR = os.path.join(DATA_DIR, 'Sentiment Scores')
SENT_FILES = glob(os.path.join(SENT_DIR, '*'))
MASTER_DIR = os.path.join(DATA_DIR, 'stanfordSentimentTreebankRaw')
SCORES_FILE = os.path.join(MASTER_DIR, 'rawscores_exp12.txt')
SENT_FILE = os.path.join(MASTER_DIR, 'sentlex_exp12.txt')


def remove_noise(tweet_tokens, stop_words=()):
    cleaned_tokens = []
    for token, tag in pos_tag(tweet_tokens):
        token = re.sub('(\'[s|v|l][e|l]?)', '', token)
        token = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|'\
                       '(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', token)
        token = re.sub('(@[A-Za-z0-9_]+)', '', token)
        if tag.startswith("NN"):
            pos = 'n'
        elif tag.startswith('VB'):
            pos = 'v'
        else:
            pos = 'a'

        lemmatizer = WordNetLemmatizer()
        token = lemmatizer.lemmatize(token, pos)
        if len(token) > 0 and token not in string.punctuation and token.lower() not in stop_words:
            cleaned_tokens.append(token.lower())

    return ' '.join(cleaned_tokens)


def evaluate(model, test_features, test_labels):
    predictions = model.predict(test_features)
    errors = abs(predictions - test_labels)
    mape = 100 * np.mean(errors / test_labels)
    accuracy = 100 - mape
    print('Model Performance')
    print('Average Error: {:0.4f} degrees.'.format(np.mean(errors)))
    print('Accuracy = {:0.2f}%.'.format(accuracy))
    return accuracy

if __name__ == '__main__':
    scores_df = pd.read_csv(SCORES_FILE, delimiter='\n', names=['scores'])
    scores_df['sent_mean'] = scores_df['scores'].apply(lambda x: np.mean([float(y) for y in x.split(',')][1:]))
    scores_df['sent_med'] = scores_df['scores'].apply(lambda x: np.median([float(y) for y in x.split(',')][1:]))
    sent_df = pd.read_csv(SENT_FILE, names=['index', 'sentence'])
    data_df = scores_df.join(sent_df)
    data_df = data_df[['sentence', 'sent_mean', 'sent_med']]

    # process data
    stop_words = stopwords.words('english')
    data_df['processed'] = data_df['sentence']
    conjugations = ["are n't", "wo n't", "do n't", "is n't", "you 're'", "ca n't"]
    subs = ['are not', 'will not', 'do not', 'is not', 'you are', 'can not']
    for substr, sbstitute in zip(conjugations, subs):
        data_df['processed'] = data_df['processed'].str.replace(substr, sbstitute, regex=False)
    noise = ['&#44', '&#96', '--', '2Â', "''", '...', '\*', '&#59', '2Â 1/2']
    for substr in noise:
        data_df['processed'] = data_df['processed'].str.replace(substr,'',regex=False)
    data_df['processed'] = [remove_noise(word_tokenize(tokens), stop_words) for tokens in data_df.processed]
    # drop nulls
    isnull = (data_df['processed'] == '') | data_df['processed'].isnull()
    data_df = data_df[~isnull].reset_index(drop=True)
    # drop dups
    while True:
        dup_mask = data_df['processed'].duplicated()
        dups = dup_mask.sum()
        if dups == 0:
            break
        data_df = data_df[~dup_mask].reset_index(drop=True)
    data_df.to_csv(os.path.join(MASTER_DIR, 'processed_data.csv'), index=False, quoting=csv.QUOTE_ALL)

    wordnet = WordNetLemmatizer()
    def tokenize(doc):
        return [wordnet.lemmatize(word) for word in word_tokenize(doc.lower())]
    tdif_vectorizer = TfidfVectorizer(stop_words='english',
                                      tokenizer=tokenize,
                                      ngram_range=(1, 3),
                                      use_idf=True)
    X = tdif_vectorizer.fit_transform(data_df.processed)
    y = data_df['sent_med']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    ######## grid search
    param_grid = {
        'bootstrap': [True],
        'max_depth': [90],
        'max_features': ['auto'],
        'min_samples_leaf': [2],
        'min_samples_split': [9, 11],
        'n_estimators': [550, 650]
    }
    # Create a based model
    rf = RandomForestRegressor()
    # Instantiate the grid search model
    grid_search = GridSearchCV(estimator=rf, param_grid=param_grid,
                               cv=3, n_jobs=-1, verbose=2)

    grid_search.fit(X_train, y_train)
    rf_model = grid_search.best_estimator_
    grid_accuracy = evaluate(rf_model, X_test, y_test)

    # store stuff
    now = pd.Timestamp.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    with open(os.path.join(MASTER_DIR, f'random_forest_{now}.p'), 'wb') as f:
        pickle.dump(rf_model, f)

    with open(os.path.join(MASTER_DIR, f'grid_search_{now}.txt'), 'w') as text:
        params = grid_search.get_params()
        del params['estimator']
        params['best_params'] = grid_search.best_params_
        json.dump(params, text)

    with open(os.path.join(MASTER_DIR, f'vectorizer_{now}.p'), 'wb') as fin:
        pickle.dump(tdif_vectorizer, fin)
