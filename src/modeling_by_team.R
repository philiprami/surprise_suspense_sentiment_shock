library(lfe)
library(plm)
library(tidyverse)

setwd("/Users/philipramirez/school_repos/surprise_suspense_sentiment/data/aggregated/team_data")
filenames = list.files(pattern="season_2013_agg_final_2022-02-21*")

for (filename in filenames) {
  out <- file("results_by_team_eff.txt", "a+")
  sink(out)

  team_data = read.csv(filename)
  selection = team_data[which(team_data$is_home == 1),]$selection_home[1]
  print(toupper(selection))

  team_frame = pdata.frame(team_data, index = c("Event.ID", "minute"))
  pdim(team_frame)

  modelA = felm(fan_tweet ~ lag(fan_tweet) + surprise_eff_prob + shock_eff_prob + suspense_eff_prob
                |Event.ID + minute,  data=team_frame)
  print(summary(modelA))

  modelB = felm(fan_retweet_tweet ~ lag(fan_retweet_tweet) + surprise_mean_prob + shock_mean_prob + suspense_mean_prob
                |Event.ID + minute,  data=team_frame)
  print(summary(modelB))

  modelC = felm(fan_tweet ~ lag(fan_tweet) + own_surprise_eff_prob + own_shock_eff_prob + own_suspense_eff_prob
                |Event.ID + minute,  data=team_frame)
  print(summary(modelC))

  modelD = felm(fan_retweet_tweet ~ lag(fan_retweet_tweet) + own_surprise_eff_prob + own_shock_eff_prob + own_suspense_eff_prob
                |Event.ID + minute,  data=team_frame)
  print(summary(modelD))

  sink()
  close(out)
}
