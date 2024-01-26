import os
import pandas as pd
from glob import glob

CWD = os.path.dirname(__file__)
DATA_DIR = os.path.join(CWD, '..', 'data')
SENTIMENT_DIR = os.path.join(DATA_DIR, 'Sentiment Scores')

all_df = pd.DataFrame(columns=['index', 'predictions', 'file_name', 'outlier'])
file_names = glob(SENTIMENT_DIR + '/*csv')
processed_files = set(all_df.file_name.unique())
for filename in file_names:
    if filename in processed_files:
        continue
    df = pd.read_csv(filename)
    if df.shape[0] > 0:
        df.reset_index(inplace=True)
        df['file_name'] = filename
        all_df = pd.concat([all_df, df[['index', 'predictions', 'file_name']]])
    processed_files.add(filename)
    print(len(processed_files))

p25 = all_df['predictions'].quantile(0.25)
p75 = all_df['predictions'].quantile(0.75)
iqr = p75 - p25
upper_limit = p75 + 1.5 * iqr
lower_limit = p25 - 1.5 * iqr
outlier_mask = (all_df['predictions'] > upper_limit) | (all_df['predictions'] < lower_limit)
all_df['outlier'] = 0
all_df.loc[outlier_mask, 'outlier'] = 1
all_df.to_csv(os.path.join(DATA_DIR, 'sentiment_outliers.csv'), index=False)
