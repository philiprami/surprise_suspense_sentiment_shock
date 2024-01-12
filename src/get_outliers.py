import pandas as pd
from glob import glob

all_df = pd.DataFrame()
for filename in file_names:
    if filename in all_df.file_name.unique():
        continue
    df = pd.read_csv(filename)
    if df.shape[0] > 0:
        df.reset_index(inplace=True)
        df['file_name'] = filename
        all_df = pd.concat([all_df, df[['index', 'predictions', 'file_name']]])

p25 = all_df['predictions'].quantile(0.25)
p75 = all_df['predictions'].quantile(0.75)
iqr = p75 - p25
upper_limit = p75 + 3 * iqr
lower_limit = p25 - 3 * iqr
outlier_mask = (all_df['predictions'] > upper_limit) | (all_df['predictions'] < lower_limit)
