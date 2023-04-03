# Exploring entertainment utility from football games
Tim Pawlowski, Dooruj Rambaccussing, Philip Ramirez, J. James Reade, Giambattista Rossi


Code repository for ["Exploring entertainment utility from football games
"](https://www.linkedin.com/in/philip-ramirez/) Here you will find the code, data, and documentation necessary to reproduce the findings in our paper. Please forward all questions/concerns to p.ramirez@pgr.reading.ac.uk.

## Data
The data sources used in this project include historical **betfair** data sourced from [Fracsoft](http://data.danetsoft.com/fracsoft.com/), match **commentaries** collected from [whoscored.com](https://www.whoscored.com), Twitter data via [API](https://developer.twitter.com/en/docs/twitter-api), and predicted **sentiment scores** released by Stanford University's [CoreNLP](https://stanfordnlp.github.io/CoreNLP/) platform (see [Code for Deeply Moving: Deep Learning for Sentiment Analysis](https://nlp.stanford.edu/sentiment/code.html) for direct dataset download).
<br />
<br />
[Google Drive: Exploring entertainment utility from football games](https://drive.google.com/drive/folders/1FkS5eJ5WltU37xnKVmXh81PvwnaizZRg?usp=sharing)

### IN
1. **betfair** - historical betfair line changes - including odds and volumes - for every English Premier League match in the 2013 season.

2. **Commentaries** - extracted form [whoscored.com](https://www.whoscored.com), match commentaries are gathered for every match of the 2013 season. This includes salient events and granular time stamps.

3. **Sentiment scores** - described as a "one stop shop for natural language processing", Stanford's CoreNLP provides public datasets that can be used for text analysis. This includes raw text as well as deep learning model predictions.

4. **Twitter** - acquired from the Twitter API using EPL team associated hashtags and handles.

### OUT
1. **Sentiment analysis** -  Using the Stanford Sentiment Treebank, a full corpus used for deep learning, we leverage the deep learning sentiment scores to train our own sentiment analysis model. Pointed to our twitter dataset, this model generates the predictions used to formulate sentiment.

2. **Match simulations** - with historical scoring rates, we derive in-play outcome probabilities by simulating goals for each minute of every match.

1. **Final** - File name: **season_2013_agg_final_processed.csv**. Dataset compiled using the acquired odds, commentaries, simulations, and twitter data. Complete with all derived emotional cues - surprise, suspense, shock, and sentiment - for each match.

## Code
All python scripts were used exclusively for model training, data compilation, processing, and merging. Regression analysis is contained within the Stata .do files. All data input files for the scripts can be found in the Google Drive link listed in the data section.

RECOMMENDED: running all steps is highly compute and time intensive. To skip to analysis and modeling (last step), simply download the final dataset and run the final do file.

**commentary_scrape**
<br />
Before any aggregations can be processed, commentaries must be scraped. Since this data only needs to be acquired once, it's kept in its own standalone project named "commentary_scrape".
```
# Note: project leverages selenium (a software QA package). In order to enable the package, first download the latest gecko driver. Store the path to the downloaded driver in your environment variables as "GECKO_DRIVER_PATH".

# To run
python commentary_scrape/src/ws_get_links.py
python commentary_scrape/src/ws_scrape_links.py
python commentary_scrape/src/ws_process_xml.py
```

**timezones.py**
<br />
python script to find timezones and corresponding utc offsets for each date/location pair found in the odds dataset
```
# To run
python timezones.py -i '/path/to/odds.dta' -o 'path/to/timezones.dta'
```

**wiki_views.py**
<br />
python script to get Wikipedia article views for every player in the manually compiled list of tennis players
```
# To run
python wiki_views.py -i '/path/to/players.csv' -o 'path/to/wikipedia.csv'
```

**elo.R**
<br />
R script to provide elo and welo ratings for every player and match time in the dataset with ranking information. Ouput is elo.dta and welo.dta
```
# To run
Rscript elo.R
```

**merge_all.do**
<br />
merges the wikipedia article views data into the odds.dta file for winners and losers. Additionally, timezones and elo/welo are merged in. The output file (final.dta) will be used for estimation and demonstration of the betting strategy.
```
# To run
do merge_all.do
```

**final.do**
<br />
stata .do file to reproduce estimations/figures found in our paper. File also includes light data manipulation/feature engineering
```
# To run
do final.do
```
