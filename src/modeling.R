library(plm)
library(gplots)
library(stargazer)
library(broom)
library(dplyr)
library(openxlsx)
library(ggplot2)
library(scales)
library(ggplot2)
library(tidyverse)
library(Rcpp)
library(magrittr)
library(tidyverse)
library(plm)
library(car)
library(tseries)
require(lmtest)
library(lfe)

setwd("/Users/philipramirez/school_repos/surprise_suspense_sentiment/data/aggregated")
data = read.csv("season_2013_agg_final_2022-02-01.csv")
data1= data %>%
  mutate(data,
         num_tweets = num_tweets_away + num_tweets_home,
         ln_numtweets = log(num_tweets),
         fan_tweets = fan_tweets_away + fan_tweets_home,
         ln_fantweets = log(fan_tweets),
         lntweetsaway = log(num_tweets_away),
         lntweetshome = log(num_tweets_home),
         ln_fantweetshome = log(fan_tweets_home),
         ln_fantweetsaway = log(fan_tweets_away))

# Lfe ---------------------------------------------------------------------

data1 = pdata.frame(data1, index = c("Event.ID", "agg_key"))
pdim(data1)

sink('results.txt')
model1a = felm(ln_numtweets ~ lag(ln_numtweets)+  surprise_eff_prob + shock_eff_prob + suspense_eff_prob|Event.ID + agg_key,
                             data = data1)
print(summary(model1a))

model2a = felm(ln_numtweets ~ lag(ln_numtweets)+  surprise_median_prob + shock_median_prob + suspense_median_prob|Event.ID + agg_key,
                                 data = data1)
print(summary(model2a))

model3a = felm(ln_numtweets ~ lag(ln_numtweets)+  surprise_mean_prob + shock_mean_prob + suspense_mean_prob|Event.ID + agg_key,
                             data = data1)
summary(model3a)

model4a = felm(lntweetsaway ~ lag(lntweetsaway)+  surprise_mean_prob + shock_mean_prob + suspense_mean_prob|Event.ID + agg_key,
                             data = data1)
summary(model4a)

model5a = felm(lntweetsaway ~ lag(lntweetsaway)+  surprise_median_prob + shock_median_prob + suspense_median_prob
               |Event.ID + agg_key,  data = data1)
summary(model5a)

model6a = felm(lntweetshome ~ lag(lntweetshome)+  surprise_mean_prob + shock_mean_prob + suspense_mean_prob
                  |Event.ID + agg_key,  data = data1)
summary(model6a)

model7a = felm(lntweetshome ~ lag(lntweetshome)+  surprise_median_prob + shock_median_prob + suspense_median_prob
                 |Event.ID + agg_key,  data = data1)
summary(model7a)

model3b = felm(ln_fantweets ~ lag(ln_fantweets)+  surprise_mean_prob + shock_mean_prob + suspense_mean_prob|Event.ID + agg_key,
               data = data1)
summary(model3b)

model4b = felm(ln_fantweetsaway ~ lag(ln_fantweetsaway)+  surprise_mean_prob + shock_mean_prob + suspense_mean_prob|Event.ID + agg_key,
               data = data1)
summary(model4b)

model6b = felm(ln_fantweetshome ~ lag(ln_fantweetshome)+  surprise_mean_prob + shock_mean_prob + suspense_mean_prob
               |Event.ID + agg_key,  data = data1)
summary(model6b)

sink()
