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
All python scripts were used exclusively for model training, data compilation, processing, and merging. Regression analysis is contained within the R scripts. All data input files for the scripts can be found in the Google Drive link listed in the data section. In order to run, download ALL data files and place them in this project in the folder named "data" (do not change any folder names). All scripts will point to this folder for data ingestion and delivery.

**RECOMMENDED:** running all steps is highly compute and time intensive (up to 5+ days of processing time). To skip to analysis and modeling (last step), simply download the final datasets in the folder named "aggregated" and run the analysis R script: src/code_jr.R

### To Run (ALL)
PREQUISITE: Please ensure pandas version 1.3.0 is installed prior to your python environment. Before any aggregations can be processed, a few one time processes must be completed: 

**1) Commentary Scrape**
```
# Note: project leverages selenium (a software QA package). In order to enable the package, first download the latest gecko driver (https://github.com/mozilla/geckodriver/releases). 
# Store the path to the downloaded driver in your environment variables as "GECKO_DRIVER_PATH". 

# To run
python commentary_scrape/src/ws_get_links.py
python commentary_scrape/src/ws_scrape_links.py
python commentary_scrape/src/ws_process_xml.py
python src/find_card_types.py
```

**2) Map Data**
```
# To run
python src/map_data.py
```

**3) Random Forest Sentiment Analysis & Fans/Haters**
```
# To run 
python src/nlp.py
python src/get_fav_teamp.py
python src/get_outliers.py
```

**4) Scoring Rates/Distribution & Match Simulations**
```
# To run
python src/get_scoring_distrib.py
python src/estimate_scoring_rates.py
python src/simulate_goals.py
```

---
#### Execute pipeline
The pipeline described in pipeline.yaml is a step wise approach to process our final dataset. Each step is executed synchronously with dependency on the previous step. The scripts, inputs, and outputs are detailed below. 
```
scripts:
  aggregate_min.py:
      output: data/aggregated/season_2013_agg_min_{{ get_date() }}.csv
  reformat_dataset.py:
      input: data/aggregated/season_2013_agg_min_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_reformatted_{{ get_date() }}.csv
  rescale.py:
      input: data/aggregated/season_2013_agg_reformatted_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_scaled_{{ get_date() }}.csv
  calculate_metrics.py:
      input: data/aggregated/season_2013_agg_scaled_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_metrics_{{ get_date() }}.csv
  cleanup_data.py:
      input: data/aggregated/season_2013_agg_metrics_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_cleaned_{{ get_date() }}.csv
  calculate_suspense.py:
      input: data/aggregated/season_2013_agg_cleaned_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_suspense_{{ get_date() }}.csv
  calculate_sim_metrics.py:
      input: data/aggregated/season_2013_agg_suspense_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_sim_results_{{ get_date() }}.csv
  recalculate_redcards.py:
      input: data/aggregated/season_2013_agg_sim_results_{{ get_date() }}.csv
      output: data/aggregated/season_2013_agg_final_{{ get_date() }}.csv
  remove_and_reorder.py:
      input: data/aggregated/season_2013_agg_final_{{ get_date() }}.csv
      ouptut: data/aggregated/season_2013_agg_final_processed_{{ get_date() }}.csv
  split_team_files.py:
      input: data/aggregated/season_2013_agg_final_processed_{{ get_date() }}.csv
      output: data/aggregated/team_data/{{ get_date() }}
```
To run simply run the run.py python script. It will read pipeline.yaml as a config file.
```
# To run 
python run.py
```
---
#### Analysis
The R scripts described are use for regression analysis and analysis by team. To run, execute the scripts "modeling.R" and "modeling_by_team.R" in an R compatible IDE such as RStudio.
