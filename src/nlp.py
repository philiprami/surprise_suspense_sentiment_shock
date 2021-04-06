import re
import csv
import nltk
import json
import string
import random
import pickle
import numpy as np
import pandas as pd
from glob import glob
# nltk.download('punkt')
# nltk.download('wordnet')
# nltk.download('twitter_samples')
# nltk.download('averaged_perceptron_tagger')
# nltk.download('stopwords')
from nltk import FreqDist
from nltk.tag import pos_tag
from nltk.corpus import stopwords
from nltk.corpus import twitter_samples
from nltk.tokenize import word_tokenize
from nltk.stem.wordnet import WordNetLemmatizer
from nltk import classify
from nltk import NaiveBayesClassifier

from sklearn.ensemble import RandomForestRegressor
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer

def remove_noise(tweet_tokens, stop_words=(), nlkt=True):
    cleaned_tokens = []
    for token, tag in pos_tag(tweet_tokens):
        token = re.sub('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+#]|[!*\(\),]|'\
                       '(?:%[0-9a-fA-F][0-9a-fA-F]))+','', token)
        token = re.sub("(@[A-Za-z0-9_]+)","", token)
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

    if nlkt:
        return cleaned_tokens
    else:
        return ' '.join(cleaned_tokens)

def get_all_words(cleaned_tokens_list):
    for tokens in cleaned_tokens_list:
        for token in tokens:
            yield token

def get_tweets_for_model(cleaned_tokens_list):
    for tweet_tokens in cleaned_tokens_list:
        yield dict([token, True] for token in tweet_tokens)

# nltk data

positive_tweets = twitter_samples.strings('positive_tweets.json')
negative_tweets = twitter_samples.strings('negative_tweets.json')
text = twitter_samples.strings('tweets.20150430-223406.json')
tweet_tokens = twitter_samples.tokenized('positive_tweets.json')
stop_words = stopwords.words('english')
positive_tweet_tokens = twitter_samples.tokenized('positive_tweets.json')
negative_tweet_tokens = twitter_samples.tokenized('negative_tweets.json')
positive_cleaned_tokens_list = [remove_noise(tokens, stop_words) for tokens in positive_tweet_tokens]
negative_cleaned_tokens_list = [remove_noise(tokens, stop_words) for tokens in negative_tweet_tokens]
all_pos_words = get_all_words(positive_cleaned_tokens_list)
freq_dist_pos = FreqDist(all_pos_words)
positive_tokens_for_model = get_tweets_for_model(positive_cleaned_tokens_list)
negative_tokens_for_model = get_tweets_for_model(negative_cleaned_tokens_list)
positive_dataset = [(tweet_dict, 1) for tweet_dict in positive_tokens_for_model]
negative_dataset = [(tweet_dict, 0) for tweet_dict in negative_tokens_for_model]
dataset = positive_dataset + negative_dataset
random.shuffle(dataset)
train_data = dataset[:8000]
test_data = dataset[8000:]

classifier = NaiveBayesClassifier.train(train_data)
print("Accuracy is:", classify.accuracy(classifier, test_data))
print(classifier.show_most_informative_features(10))
custom_tweet = "I ordered just once from TerribleCo, they screwed up, never used the app again."
custom_tokens = remove_noise(word_tokenize(custom_tweet))
print(custom_tweet, classifier.classify(dict([token, True] for token in custom_tokens)))

# sklearn w/ nltk data
wordnet = WordNetLemmatizer()
def tokenize(doc):
    return [wordnet.lemmatize(word) for word in word_tokenize(doc.lower())]

stop_words = stopwords.words('english')

tdif_vectorizer = TfidfVectorizer(stop_words='english',
                                  ngram_range=(1, 3),
                                  tokenizer=tokenize)
                                  #use_idf=True)

positive_tweet_tokens = twitter_samples.tokenized('positive_tweets.json')
negative_tweet_tokens = twitter_samples.tokenized('negative_tweets.json')

positive_cleaned_tokens_list = [remove_noise(tokens, stop_words, nlkt=False) for tokens in positive_tweet_tokens]
negative_cleaned_tokens_list = [remove_noise(tokens, stop_words, nlkt=False) for tokens in negative_tweet_tokens]

X = tdif_vectorizer.fit_transform(positive_cleaned_tokens_list + negative_cleaned_tokens_list)
y = [1]*len(positive_cleaned_tokens_list)+[0]*len(negative_cleaned_tokens_list)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

rf = RandomForestRegressor(verbose=1)
rf.fit(X_train, y_train)

for filename in SENT_FILES:
    df = pd.read_csv(filename)
    processed = [remove_noise(word_tokenize(tokens), stop_words, nlkt=False) for tokens in df.tweet]
    vectorized = tdif_vectorizer.transform(processed)
    predictions = rf.predict(vectorized)
    df['predictions'] = predictions

mnb = MultinomialNB()
mnb.fit(X_train, y_train)
print('Accuracy:', mnb.score(X_test, y_test))


######## stanford data

DATA_DIR = 'data/'
SENT_DIR = DATA_DIR + 'Sentiment Scores/'
SENT_FILES = glob(SENT_DIR + '*')

MASTER_DIR = DATA_DIR + 'stanfordSentimentTreebankRaw/'
SCORES_FILE = MASTER_DIR + 'rawscores_exp12.txt'
SENT_FILE = MASTER_DIR + 'sentlex_exp12.txt'

scores_df = pd.read_csv(SCORES_FILE, delimiter='\n', names=['scores'])
scores_df['sent_mean'] = scores_df['scores'].apply(lambda x: np.mean([float(y) for y in x.split(',')][1:]))
sent_df = pd.read_csv(SENT_FILE, names=['index','sentence'])
data_df = scores_df.join(sent_df)
data_df = data_df[['sentence', 'sent_mean']]

stop_words = stopwords.words('english')
processed = [remove_noise(word_tokenize(tokens), stop_words, nlkt=False) for tokens in data_df.sentence]
wordnet = WordNetLemmatizer()
def tokenize(doc):
    return [wordnet.lemmatize(word) for word in word_tokenize(doc.lower())]
tdif_vectorizer = TfidfVectorizer(stop_words='english',
                                  tokenizer=tokenize)
X = tdif_vectorizer.fit_transform(processed)
with open('models/vectorizer.p', 'wb') as fin:
    pickle.dump(tdif_vectorizer, fin)

y = data_df['sent_mean']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

##### random_forest_oob

# rf = RandomForestRegressor(verbose=1)
# rf.fit(X_train, y_train)
# with open('models/random_forest_oob.p', 'wb') as f:
#     pickle.dump(rf, f)

######## grid search
rf_grid = {
            'n_estimators': [100, 150, 200],
            'max_features' : ['sqrt', 'log2'],
            # 'scoring' : ['r2'],
            'n_jobs' : [4],
            'verbose' : [1]
           }

rf_gridsearch = GridSearchCV(RandomForestRegressor(verbose=1), rf_grid)
rf_gridsearch.fit(X_train, y_train)
rf_model = rf_gridsearch.best_estimator_

# store stuff
now = pd.Timestamp.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
with open(f'models/random_forest_{now}.p', 'wb') as f:
    pickle.dump(rf_model, f)

with open(f'models/grid_search_{now}.txt', 'w') as text:
    params = rf_gridsearch.get_params()
    del params['estimator']
    params['best_params'] = rf_gridsearch.best_params_
    json.dump(params, text)

with open(f'models/vectorizer_{now}.p', 'wb') as fin:
    pickle.dump(tdif_vectorizer, fin)

######## implement predictions
processed_files = set()
for filename in SENT_FILES:
    if filename in processed_files:
        continue

    try:
        df = pd.read_csv(filename)
        processed_ = [remove_noise(word_tokenize(tokens), stop_words, nlkt=False) for tokens in df.tweet]
        vectorized = tdif_vectorizer.transform(processed_)
        predictions = rf_model.predict(vectorized)
        df['predictions'] = predictions
        df.to_csv(filename, index=False, quoting=csv.QUOTE_ALL)
        processed_files.add(filename)
    except:
        pass
