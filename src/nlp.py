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
SENT_OUT_DIR = SENT_DIR + ' 11_20'
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

    from sklearn import metrics
    print('Mean Absolute Error (MAE):', metrics.mean_absolute_error(test_labels, predictions))
    print('Mean Squared Error (MSE):', metrics.mean_squared_error(test_labels, predictions))
    print('Root Mean Squared Error (RMSE):', np.sqrt(metrics.mean_squared_error(test_labels, predictions)))
    mape = np.mean(np.abs((test_labels - predictions) / np.abs(test_labels)))
    print('Mean Absolute Percentage Error (MAPE):', round(mape * 100, 2))
    print('Accuracy:', round(100*(1 - mape), 2))

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
    data_df['training'] = 1

    # add twitter sentences to include in vectorizer
    for filename in SENT_FILES:
        df = pd.read_csv(filename)
        df['training'] = 0
        df = df[['tweet', 'training']].rename(columns={'tweet':'sentence'})
        df['sent_mean'] = None
        df['sent_med'] = None
        data_df = data_df.append(df)

    # process data
    data_df['processed'] = data_df['sentence']
    stop_words = stopwords.words('english')
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
    # data_df.to_csv(os.path.join(MASTER_DIR, 'processed_data.txt'), sep='\t', index=False, quoting=3)

    def tokenize(doc):
        return [word for word in word_tokenize(doc.lower())]
    tdif_vectorizer = TfidfVectorizer(stop_words='english',
                                      tokenizer=tokenize)
    training_mask = data_df['training'] == 1
    X = tdif_vectorizer.fit_transform(data_df.processed)
    x = tdif_vectorizer.transform(data_df[training_mask].processed)
    y = data_df[training_mask]['sent_med']
    X_train, X_test, y_train, y_test = train_test_split(x, y, test_size=0.2)

    ######## grid search
    param_grid = {
        'max_depth': [2000, 2500, 3000],
        'max_features': ['sqrt'],
        'min_samples_leaf': [2],
        'min_samples_split': [7],
        'n_estimators': [550]
    }
    grid_search = GridSearchCV(estimator=RandomForestRegressor(), param_grid=param_grid,
                               cv=4, verbose=2, n_jobs=4)

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
        params['accuracy'] = grid_accuracy
        json.dump(params, text)

    with open(os.path.join(MASTER_DIR, f'vectorizer_{now}.p'), 'wb') as fin:
        pickle.dump(tdif_vectorizer, fin)

    # apply model predictions to data
    os.makedirs(SENT_OUT_DIR, exist_ok=True)
    processed_files = set()
    for filename in SENT_FILES:
        if filename in processed_files:
            continue

        df = pd.read_csv(filename)
        df['processed'] = df['tweet']
        for substr, sbstitute in zip(conjugations, subs):
            df['processed'] = df['processed'].str.replace(substr, sbstitute, regex=False)
        for substr in noise:
            df['processed'] = df['processed'].str.replace(substr,'',regex=False)
        df['processed'] = [remove_noise(word_tokenize(tokens), stop_words) for tokens in df.processed]
        if df['processed'].shape[0] == 0:
            continue
        vectors = tdif_vectorizer.transform(df.processed)
        df['predictions'] = rf_model.predict(vectors)
        df.to_csv(os.path.join(SENT_OUT_DIR, os.path.split(filename)[1]), index=False, quoting=csv.QUOTE_ALL)
        processed_files.add(filename)
        del df
        del vectors

    # feature importance
    # after grid search is done
    best_params = {"bootstrap": True, "max_depth": 90, "max_features": "auto", "min_samples_leaf": 2, "min_samples_split": 9, "n_estimators": 550}
    rf = RandomForestRegressor(**best_params, verbose=2, n_jobs=3)
    rf.fit(X_train, y_train)

    accuracy = evaluate(rf, X_test, y_test)
    feature_importances = rf.feature_importances_
    tdif_features = tdif_vectorizer.get_feature_names()
    sorted_features = sorted(zip(tdif_features, feature_importances), key=itemgetter(-1), reverse=True)
    feature_df = pd.DataFrame.from_records(sorted_features, columns =['token', 'importance'])

    fn=data.feature_names
    cn=data.target_names
    import matplotlib.pyplot as plt
    from sklearn import tree
    fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=800)
    tree.plot_tree(rf.estimators_[0],
                   feature_names=tdif_features,
                   filled = True);
    fig.savefig('rf_individualtree.png')

    # https://www.analyticsvidhya.com/blog/2021/06/understanding-random-forest/
    # https://www.projectpro.io/recipes/use-tf-df-vectorizer
    # https://stackoverflow.com/questions/40155128/plot-trees-for-a-random-forest-in-python-with-scikit-learn
