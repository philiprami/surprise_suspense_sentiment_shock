source("~/Dropbox/Research/Sport/Correct-score/code/forecasting-code-2022-08.R")
#rm(list =ls())
library(plm)
library(gplots)
library(stargazer)
library(broom)
library(dplyr)
library(openxlsx)
library(ggplot2)
library(scales)
library(tidyverse)
library(Rcpp)
library(lfe)

fileloc = "/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/"
# fileloc = "C:/Users/Tim Pawlowski/Dropbox/Suprise, suspense and sentiment from Twitter/Datasets/"

# data = read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/season_2013_agg_final_processed_2022-07-21.csv",stringsAsFactors = FALSE)
data = read.csv(paste0(fileloc,"season_2013_agg_final_processed_random_forest_2024-01-11.csv"),stringsAsFactors = FALSE)
data.T = read.csv(paste0(fileloc,"season_2013_agg_final_processed_tformer_2024-01-18.csv"),stringsAsFactors = FALSE)
data.B = read.csv(paste0(fileloc,"season_2013_agg_final_processed_both_2024-01-16.csv"),stringsAsFactors = FALSE)

match.summaries <- data[duplicated(data$Event.ID)==FALSE,c("Event.ID","selection_home","selection_away","Date")]

tweets.ars.08.17 = read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Sentiment Scores NLP/epl-Arsenal-2013-08-24.csv",stringsAsFactors = FALSE)
tweetloc <- "/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Sentiment Scores NLP/"
tweets.files <- list.files(tweetloc)
tweet.ids <- data.frame(stringsAsFactors = FALSE)
for(tt in tweets.files) {
   print(tt)
   temp <- read.csv(paste0(tweetloc,tt),stringsAsFactors = FALSE)
   temp$filename <- tt
   tweet.ids <- rbind(tweet.ids,temp[,c("tweeter_id","filename")])
}
tweet.ids$const=1
tweet.ids$team <- gsub("^epl-(.*?)-(\\d{4}-\\d{2}-\\d{2})[.]csv$","\\1",tweet.ids$filename)
tweet.ids$date <- as.Date(gsub("^epl-(\\S+)-(\\d{4}-\\d{2}-\\d{2})[.]csv$","\\2",tweet.ids$filename))
tweet.ids2 <- merge(tweet.ids,match.summaries,by.x=c("team","date"),by.y=c("selection_home","Date"),all.x=TRUE)
tweet.ids2 <- merge(tweet.ids2,match.summaries,by.x=c("team","date"),by.y=c("selection_away","Date"),all.x=TRUE)
tweet.ids2$opponent[is.na(tweet.ids2$selection_away)==FALSE] <- tweet.ids2$selection_away[is.na(tweet.ids2$selection_away)==FALSE]
tweet.ids2$opponent[is.na(tweet.ids2$selection_home)==FALSE] <- tweet.ids2$selection_home[is.na(tweet.ids2$selection_home)==FALSE]

match.tweets <- aggregate(tweet.ids$const[duplicated(tweet.ids$tweeter_id)==FALSE],
                          by=list(tweet.ids$filename[duplicated(tweet.ids$tweeter_id)==FALSE]),FUN=sum)
match.tweets$team <- gsub("^epl-(.*?)-(\\d{4}-\\d{2}-\\d{2})[.]csv$","\\1",match.tweets$Group.1)
match.tweets$date <- as.Date(gsub("^epl-(.*?)-(\\d{4}-\\d{2}-\\d{2})[.]csv$","\\2",match.tweets$Group.1))
match.tweets <- merge(match.tweets,match.summaries,by.x=c("team","date"),by.y=c("selection_home","Date"),all.x=TRUE)
match.tweets <- merge(match.tweets,match.summaries,by.x=c("team","date"),by.y=c("selection_away","Date"),all.x=TRUE)
match.tweets$opponent[is.na(match.tweets$selection_away)==FALSE] <- match.tweets$selection_away[is.na(match.tweets$selection_away)==FALSE]
match.tweets$opponent[is.na(match.tweets$selection_home)==FALSE] <- match.tweets$selection_home[is.na(match.tweets$selection_home)==FALSE]
match.tweets$Event.ID[is.na(match.tweets$Event.ID.x)==FALSE] <- match.tweets$Event.ID.x[is.na(match.tweets$Event.ID.x)==FALSE]
match.tweets$Event.ID[is.na(match.tweets$Event.ID.y)==FALSE] <- match.tweets$Event.ID.y[is.na(match.tweets$Event.ID.y)==FALSE]
match.tweets$match[is.na(match.tweets$selection_away)==FALSE] <- paste0(match.tweets$team[is.na(match.tweets$selection_away)==FALSE]," v ",match.tweets$selection_away[is.na(match.tweets$selection_away)==FALSE])
match.tweets$match[is.na(match.tweets$selection_home)==FALSE] <- paste0(match.tweets$selection_home[is.na(match.tweets$selection_home)==FALSE]," v ",match.tweets$team[is.na(match.tweets$selection_home)==FALSE])
match.tweets <- match.tweets[order(match.tweets$Event.ID),]

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/tweet-numbers-by-match-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
plot(1:NROW(match.tweets[is.na(match.tweets$selection_away)==TRUE,]),match.tweets$x[is.na(match.tweets$selection_away)==TRUE],type="h",
     ylim=range(match.tweets$x),xaxt="n",xlab="Match",ylab="No. of Tweets",
     main = "Tweets per match, per team, EPL 2013/14",
     sub = "red = away, black = home")
lines(c(1:NROW(match.tweets[is.na(match.tweets$selection_home)==TRUE,]))+0.5,match.tweets$x[is.na(match.tweets$selection_home)==TRUE],type="h",col=2)
axis(side=1,at=1:NROW(match.tweets[is.na(match.tweets$selection_home)==TRUE,]),
     labels=match.tweets$match[is.na(match.tweets$selection_home)==TRUE],las=2,cex.axis=0.25)
dev.off()

data$num_tweets_home[is.na(data$num_tweets_home)==TRUE] <- 0
data$num_tweets_away[is.na(data$num_tweets_away)==TRUE] <- 0
data$num_tweets_total <- data$num_tweets_home + data$num_tweets_away

data$fan_tweets_home[is.na(data$fan_tweets_home)==TRUE] <- 0
data$fan_tweets_away[is.na(data$fan_tweets_away)==TRUE] <- 0
data$fan_tweets_total <- data$fan_tweets_home + data$fan_tweets_away

data$hater_tweets_home[is.na(data$hater_tweets_home)==TRUE] <- 0
data$hater_tweets_away[is.na(data$hater_tweets_away)==TRUE] <- 0
data$hater_tweets_total <- data$hater_tweets_home + data$hater_tweets_away

data$neutral_tweets_home <- data$num_tweets_home - data$hater_tweets_home - data$fan_tweets_home
data$neutral_tweets_away <- data$num_tweets_away - data$hater_tweets_away - data$fan_tweets_away
data$neutral_tweets_total <- data$neutral_tweets_home + data$neutral_tweets_away

data.B$num_tweets_home[is.na(data.B$num_tweets_home)==TRUE] <- 0
data.B$num_tweets_away[is.na(data.B$num_tweets_away)==TRUE] <- 0
data.B$num_tweets_total <- data.B$num_tweets_home + data.B$num_tweets_away

data.B$fan_tweets_home[is.na(data.B$fan_tweets_home)==TRUE] <- 0
data.B$fan_tweets_away[is.na(data.B$fan_tweets_away)==TRUE] <- 0
data.B$fan_tweets_total <- data.B$fan_tweets_home + data.B$fan_tweets_away

data.B$hater_tweets_home[is.na(data.B$hater_tweets_home)==TRUE] <- 0
data.B$hater_tweets_away[is.na(data.B$hater_tweets_away)==TRUE] <- 0
data.B$hater_tweets_total <- data.B$hater_tweets_home + data.B$hater_tweets_away

data.B$neutral_tweets_home <- data.B$num_tweets_home - data.B$hater_tweets_home - data.B$fan_tweets_home
data.B$neutral_tweets_away <- data.B$num_tweets_away - data.B$hater_tweets_away - data.B$fan_tweets_away
data.B$neutral_tweets_total <- data.B$neutral_tweets_home + data.B$neutral_tweets_away

data.T$num_tweets_home[is.na(data.T$num_tweets_home)==TRUE] <- 0
data.T$num_tweets_away[is.na(data.T$num_tweets_away)==TRUE] <- 0
data.T$num_tweets_total <- data.T$num_tweets_home + data.T$num_tweets_away

data.T$fan_tweets_home[is.na(data.T$fan_tweets_home)==TRUE] <- 0
data.T$fan_tweets_away[is.na(data.T$fan_tweets_away)==TRUE] <- 0
data.T$fan_tweets_total <- data.T$fan_tweets_home + data.T$fan_tweets_away

data.T$hater_tweets_home[is.na(data.T$hater_tweets_home)==TRUE] <- 0
data.T$hater_tweets_away[is.na(data.T$hater_tweets_away)==TRUE] <- 0
data.T$hater_tweets_total <- data.T$hater_tweets_home + data.T$hater_tweets_away

data.T$neutral_tweets_home <- data.T$num_tweets_home - data.T$hater_tweets_home - data.T$fan_tweets_home
data.T$neutral_tweets_away <- data.T$num_tweets_away - data.T$hater_tweets_away - data.T$fan_tweets_away
data.T$neutral_tweets_total <- data.T$neutral_tweets_home + data.T$neutral_tweets_away

#data$minute <- sequence(rle(data$Inplay.flag)$lengths)

##NEED TO SPLIT OUT HALF TIME
data$halftime <- as.numeric(data$minute==45 & regexpr("end",data$event_home)>-1)-as.numeric(data$minute==46 & regexpr("start",data$event_home)>-1)
data$halftime[is.na(data$halftime)==TRUE] <- 0
data$halftime <- cumsum(data$halftime)

data$injurytime <- as.numeric(is.na(data$minute)==FALSE & ((duplicated(data[,c("Course","minute")])==1 & data$halftime==0) | data$minute==91))

data$lnum_tweets_home <- log(data$num_tweets_home+0.0000001)
data$lnum_tweets_away <- log(data$num_tweets_away+0.0000001)
data$lnum_tweets_total <- log(data$num_tweets_total+0.0000001)


data$lfan_tweets_home <- log(data$fan_tweets_home+0.0000001)
data$lfan_tweets_away <- log(data$fan_tweets_away+0.0000001)
data$lfan_tweets_total <- log(data$fan_tweets_total+0.0000001)


data$lhater_tweets_home <- log(data$hater_tweets_home+0.0000001)
data$lhater_tweets_away <- log(data$hater_tweets_away+0.0000001)
data$lhater_tweets_total <- log(data$hater_tweets_total+0.0000001)

data$lneutral_tweets_home <- log(data$neutral_tweets_home+0.0000001)
data$lneutral_tweets_away <- log(data$neutral_tweets_away+0.0000001)
data$lneutral_tweets_total <- log(data$neutral_tweets_total+0.0000001)


data <- data[order(data$Course,data$minute),]
for(ll in 1:40) {
  data[[paste0("lag",ll,".Course")]] <- c(rep("NA",ll),data$Course[-seq(NROW(data)-ll+1,NROW(data))])
  data[[paste0("lag",ll,".num_tweets_home")]] <- c(rep(NA,ll),data$num_tweets_home[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".num_tweets_home")] <- NA
  data[[paste0("lag",ll,".num_tweets_away")]] <- c(rep(NA,ll),data$num_tweets_away[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".num_tweets_away")] <- NA
  data[[paste0("lag",ll,".num_tweets_total")]] <- c(rep(NA,ll),data$num_tweets_total[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".num_tweets_total")] <- NA
  data[[paste0("lag",ll,".lnum_tweets_home")]] <- c(rep(NA,ll),data$lnum_tweets_home[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lnum_tweets_home")] <- NA
  data[[paste0("lag",ll,".lnum_tweets_away")]] <- c(rep(NA,ll),data$lnum_tweets_away[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lnum_tweets_away")] <- NA
  data[[paste0("lag",ll,".lnum_tweets_total")]] <- c(rep(NA,ll),data$lnum_tweets_total[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lnum_tweets_total")] <- NA
  data[[paste0("lag",ll,".lfan_tweets_home")]] <- c(rep(NA,ll),data$lfan_tweets_home[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lfan_tweets_home")] <- NA
  data[[paste0("lag",ll,".lfan_tweets_away")]] <- c(rep(NA,ll),data$lfan_tweets_away[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lfan_tweets_away")] <- NA
  data[[paste0("lag",ll,".lfan_tweets_total")]] <- c(rep(NA,ll),data$lfan_tweets_total[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lfan_tweets_total")] <- NA
  data[[paste0("lag",ll,".lhater_tweets_home")]] <- c(rep(NA,ll),data$lhater_tweets_home[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lhater_tweets_home")] <- NA
  data[[paste0("lag",ll,".lhater_tweets_away")]] <- c(rep(NA,ll),data$lhater_tweets_away[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lhater_tweets_away")] <- NA
  data[[paste0("lag",ll,".lhater_tweets_total")]] <- c(rep(NA,ll),data$lhater_tweets_total[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lhater_tweets_total")] <- NA
  data[[paste0("lag",ll,".lneutral_tweets_home")]] <- c(rep(NA,ll),data$lneutral_tweets_home[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lneutral_tweets_home")] <- NA
  data[[paste0("lag",ll,".lneutral_tweets_away")]] <- c(rep(NA,ll),data$lneutral_tweets_away[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lneutral_tweets_away")] <- NA
  data[[paste0("lag",ll,".lneutral_tweets_total")]] <- c(rep(NA,ll),data$lneutral_tweets_total[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".lneutral_tweets_total")] <- NA
  data[[paste0("lag",ll,".sim_surprise")]] <- c(rep(NA,ll),data$sim_surprise[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".sim_surprise")] <- NA
  data[[paste0("lag",ll,".sim_shock")]] <- c(rep(NA,ll),data$sim_shock[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".sim_shock")] <- NA
  data[[paste0("lag",ll,".sim_suspense")]] <- c(rep(NA,ll),data$sim_suspense[-seq(NROW(data)-ll+1,NROW(data))])
  data[data[,paste0("lag",ll,".Course")]!=data$Course,paste0("lag",ll,".sim_suspense")] <- NA
}

summary(modelH <- felm(num_tweets_home ~ lag1.num_tweets_home + surprise + shock + suspense
                                         | Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelHsim <- lfe::felm(num_tweets_home ~ lag1.num_tweets_home + sim_surprise + sim_shock + sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelA <- lfe::felm(num_tweets_away ~ lag1.num_tweets_away + surprise + shock + suspense
              |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelAsim <- lfe::felm(num_tweets_away ~ lag1.num_tweets_away + sim_surprise + sim_shock + sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelTot <- lfe::felm(num_tweets_total ~ lag1.num_tweets_total + surprise + shock + suspense
              |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelTotsim <- lfe::felm(num_tweets_total ~ lag1.num_tweets_total + sim_surprise + sim_shock + sim_suspense
                              |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
stargazer::stargazer(modelH,modelA,modelTot)


summary(modelHl <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + surprise + shock + suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelHlsim <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + sim_surprise + sim_shock + sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelAl <- lfe::felm(lnum_tweets_away ~ lag1.lnum_tweets_away + surprise + shock + suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelAlsim <- lfe::felm(lnum_tweets_away ~ lag1.lnum_tweets_away + sim_surprise + sim_shock + sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelBl <- lfe::felm(lnum_tweets_total ~ lag1.lnum_tweets_total + surprise + shock + suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(modelBlsim <- lfe::felm(lnum_tweets_total ~ lag1.lnum_tweets_total + sim_surprise + sim_shock + sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
stargazer::stargazer(modelHl,modelHlsim,modelAl,modelAlsim,modelBl,modelBlsim)

summary(fanmodelHl <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + surprise + shock + suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fanmodelHlsim <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + sim_surprise + sim_shock + sim_suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fanmodelAl <- lfe::felm(lfan_tweets_away ~ lag1.lfan_tweets_away + surprise + shock + suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fanmodelAlsim <- lfe::felm(lfan_tweets_away ~ lag1.lfan_tweets_away + sim_surprise + sim_shock + sim_suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fanmodelBl <- lfe::felm(lfan_tweets_total ~ lag1.lfan_tweets_total + surprise + shock + suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fanmodelBlsim <- lfe::felm(lfan_tweets_total ~ lag1.lfan_tweets_total + sim_surprise + sim_shock + sim_suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
stargazer::stargazer(fanmodelHl,fanmodelHlsim,fanmodelAl,fanmodelAlsim,fanmodelBl,fanmodelBlsim)

stargazer::stargazer(modelHl,fanmodelHl,modelAl,fanmodelAl,modelBl,fanmodelBl)


summary(neutralmodelBl <- lfe::felm(lneutral_tweets_total ~ lag1.lneutral_tweets_total + surprise + shock + suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(neutralmodelBlsim <- lfe::felm(lneutral_tweets_total ~ lag1.lneutral_tweets_total + sim_surprise + sim_shock + sim_suspense
                                   |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))

summary(hatermodelBl <- lfe::felm(lhater_tweets_total ~ lag1.lhater_tweets_total + surprise + shock + suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(hatermodelBlsim <- lfe::felm(lhater_tweets_total ~ lag1.lhater_tweets_total + sim_surprise + sim_shock + sim_suspense
                                   |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))

stargazer::stargazer(modelBl,fanmodelBl,hatermodelBl,neutralmodelBl)
stargazer::stargazer(modelBlsim,fanmodelBlsim,hatermodelBlsim,neutralmodelBlsim)

##want to just focus on all tweets
data$goal1 <- as.numeric(regexpr("goal",data$event_home)>-1)
data$goal2 <- as.numeric(regexpr("goal",data$event_away)>-1)
data$goal <- data$goal1 + data$goal2
data$shot1 <- as.numeric(regexpr("shot|attempt",data$event_home)>-1)
data$shot2 <- as.numeric(regexpr("shot|attempt",data$event_away)>-1)
data$shot <- data$shot1 + data$shot2
data$woodwork1 <- as.numeric(regexpr("woodwork",data$event_home)>-1)
data$woodwork2 <- as.numeric(regexpr("woodwork",data$event_away)>-1)
data$woodwork <- data$woodwork1 + data$woodwork2
data$corner1 <- as.numeric(regexpr("corner",data$event_home)>-1)
data$corner2 <- as.numeric(regexpr("corner",data$event_away)>-1)
data$corner <- data$corner1 + data$corner2
data$yellow1 <- as.numeric(regexpr("yellow",data$event_home)>-1)
data$yellow2 <- as.numeric(regexpr("yellow",data$event_away)>-1)
data$yellow <- data$yellow1 + data$yellow2
data$red1 <- as.numeric(regexpr("red",data$event_home)>-1)
data$red2 <- as.numeric(regexpr("red",data$event_away)>-1)
data$red <- data$red1 + data$red2
data$substitution1 <- as.numeric(regexpr("substitution",data$event_home)>-1)
data$substitution2 <- as.numeric(regexpr("substitution",data$event_away)>-1)
data$substitution <- data$substitution1 + data$substitution2
data$offside1 <- as.numeric(regexpr("offside",data$event_home)>-1)
data$offside2 <- as.numeric(regexpr("offside",data$event_away)>-1)
data$offside <- data$offside1 + data$offside2
data$save1 <- as.numeric(regexpr("save",data$event_home)>-1)
data$save2 <- as.numeric(regexpr("save",data$event_away)>-1)
data$save <- data$save1 + data$save2

stargazer(data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,
               c("goal1","goal2","shot1","shot2","woodwork1","woodwork2","corner1","corner2",
                 "yellow1","yellow2","red1","red2","substitution1","substitution2",
                 "offside1","offside2","save1","save2")])

stargazer(data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,
               c("prob_home","prob_draw","prob_away","sim_prob_home","sim_prob_draw","sim_prob_away")],
          covariate.labels = c("P(home)","P(draw)","P(away)",
                               "Simulated P(home)","Simulated P(draw)","Simulated P(away)"))

stargazer(data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,
               c("sentiment_home","sentiment_away")],
          covariate.labels = c("Tweet Sentiment Home Team","Tweet Sentiment Away Team"))

stargazer(data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,
               c("suspense","sim_suspense","surprise","sim_surprise","shock","sim_shock")],
          covariate.labels = c("Suspense","Simulated Suspense","Surprise",
                               "Simulated Surprise","Shock","Simulated Shock"))

data$sq.diff <- (data$prob_home - data$prob_away)^2
data$sim.sq.diff <- (data$sim_prob_home - data$sim_prob_away)^2

data$goals1 <- ave(data$goal1, data$Event.ID, FUN=cumsum)
data$goals2 <- ave(data$goal2, data$Event.ID, FUN=cumsum)
data$totalgoals <- data$goals1 + data$goals2
data$goaldiff <- data$goals1 - data$goals2



summary(model0.0 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model0 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model1 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model2 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model3 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model4 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + sim_surprise + sim_shock + sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model4b <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model4c <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model4d <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model4e <- lfe::felm(lnum_tweets_home ~ lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model5 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(model6 <- lfe::felm(lnum_tweets_home ~ lag1.lnum_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
stargazer::stargazer(model2,model3,model6, #model0.0,model0,model1,,model4,model4c
                     covariate.labels = c("Lagged Log Total Number of Home Tweets",
                                          "Goal","Shot","Shot hit goalframe","Corner","Yellow Card",
                                          "Red Card","Substitution","Square Difference in Probabilities",
                                          "P(Draw)","Total Goals","Goal Difference","Simulated Surprise",
                                          "Simulated Shock","Simulated Suspense","Lagged Simulated Surprise",
                                          "Lagged Simulated Shock","Lagged Simulated Suspense"))

###run models with lags


summary(fanmodel0.0 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel0 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel1 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel2 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel3 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel4 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home +sim_surprise + sim_shock +sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel4b <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel4c <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel4d <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel4e <- lfe::felm(lfan_tweets_home ~ lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel5 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(fanmodel6 <- lfe::felm(lfan_tweets_home ~ lag1.lfan_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
stargazer::stargazer(fanmodel2,fanmodel3,fanmodel6,
  #fanmodel0.0,fanmodel0,fanmodel1,fanmodel2,fanmodel3,fanmodel4,fanmodel4c,
                     covariate.labels = c("Lagged Log Total Number of Home Tweets by Fans",
                                          "Goal","Shot","Shot hit goalframe","Corner","Yellow Card",
                                          "Red Card","Substitution","Square Difference in Probabilities",
                                          "P(Draw)","Total Goals","Goal Difference","Simulated Surprise",
                                          "Simulated Shock","Simulated Suspense","Lagged Simulated Surprise",
                                          "Lagged Simulated Shock","Lagged Simulated Suspense"))

##do lags 1 to 1+2+...+40, collect into a list
reglist <- list()
ii=0
depvars <- c("lag1.lfan_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense")
modform <-as.formula(paste(paste("lfan_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
summary(reglist[[paste0("fanreg.lag",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))

depvars <- c("lag1.lhater_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense")
modform <-as.formula(paste(paste("lhater_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
summary(reglist[[paste0("haterreg.lag",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))

depvars <- c("lag1.lneutral_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense")
modform <-as.formula(paste(paste("lneutral_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
summary(reglist[[paste0("neutralreg.lag",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))

for(ii in 1:40) {
  print(ii)
  depvars <- c("lag1.lfan_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff",paste0("lag",ii,".sim_surprise"),paste0("lag",ii,".sim_shock"),paste0("lag",ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lfan_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("fanreg.lag",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lhater_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff",paste0("lag",ii,".sim_surprise"),paste0("lag",ii,".sim_shock"),paste0("lag",ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lhater_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("haterreg.lag",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lneutral_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff",paste0("lag",ii,".sim_surprise"),paste0("lag",ii,".sim_shock"),paste0("lag",ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lneutral_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("neutralreg.lag",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))

  #keep contemporaneous variable
  depvars <- c("lag1.lfan_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense",paste0("lag",ii,".sim_surprise"),paste0("lag",ii,".sim_shock"),paste0("lag",ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lfan_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("fanreg.lag0and",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))

  depvars <- c("lag1.lhater_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense",paste0("lag",ii,".sim_surprise"),paste0("lag",ii,".sim_shock"),paste0("lag",ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lhater_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("haterreg.lag0and",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lneutral_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense",paste0("lag",ii,".sim_surprise"),paste0("lag",ii,".sim_shock"),paste0("lag",ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lneutral_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("neutralreg.lag0and",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))

  #keep all lags
  depvars <- c("lag1.lfan_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense",paste0("lag",1:ii,".sim_surprise"),paste0("lag",1:ii,".sim_shock"),paste0("lag",1:ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lfan_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("fanreg.lag0.",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lhater_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense",paste0("lag",1:ii,".sim_surprise"),paste0("lag",1:ii,".sim_shock"),paste0("lag",1:ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lhater_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("haterreg.lag0.",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lneutral_tweets_home","goal","shot","woodwork","corner","yellow","red","substitution","sim.sq.diff","sim_prob_draw","totalgoals","goaldiff","sim_surprise","sim_shock","sim_suspense",paste0("lag",1:ii,".sim_surprise"),paste0("lag",1:ii,".sim_shock"),paste0("lag",1:ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lneutral_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("neutralreg.lag0.",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  #keep all lags no controls
  depvars <- c("lag1.lfan_tweets_home","sim_surprise","sim_shock","sim_suspense",paste0("lag",1:ii,".sim_surprise"),paste0("lag",1:ii,".sim_shock"),paste0("lag",1:ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lfan_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("fanreg.lag0.nc.",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lhater_tweets_home","sim_surprise","sim_shock","sim_suspense",paste0("lag",1:ii,".sim_surprise"),paste0("lag",1:ii,".sim_shock"),paste0("lag",1:ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lhater_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("haterreg.lag0.nc.",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
  
  depvars <- c("lag1.lneutral_tweets_home","sim_surprise","sim_shock","sim_suspense",paste0("lag",1:ii,".sim_surprise"),paste0("lag",1:ii,".sim_shock"),paste0("lag",1:ii,".sim_suspense"))
  modform <-as.formula(paste(paste("lneutral_tweets_home", paste(depvars, collapse=" + "), sep="~"),"Event.ID + minute",sep=" | "))
  summary(reglist[[paste0("neutralreg.lag0.nc.",ii)]] <- lfe::felm(modform,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
}

plot(0:40,seq(0,12,length=41),col="white",main="Surprise (just lag)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag",ii)]]$coefficients[13],type="p",col="green") #surprise
  lines(ii,reglist[[paste0("haterreg.lag",ii)]]$coefficients[13],type="p",col="red") #surprise
  lines(ii,reglist[[paste0("neutralreg.lag",ii)]]$coefficients[13],type="p",col="black") #surprise
}

plot(0:40,seq(0,12,length=41),col="white",main="Surprise (lag and contemp)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag0and",ii)]]$coefficients[16],type="p",col="green") #surprise
  lines(ii,reglist[[paste0("haterreg.lag0and",ii)]]$coefficients[16],type="p",col="red") #surprise
  lines(ii,reglist[[paste0("neutralreg.lag0and",ii)]]$coefficients[16],type="p",col="black") #surprise
}

plot(0:40,seq(0,12,length=41),col="white",main="Surprise (all lags)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_surprise")],type="p",col="green") #surprise
  lines(ii,reglist[[paste0("haterreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_surprise")],type="p",col="red") #surprise
  lines(ii,reglist[[paste0("neutralreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_surprise")],type="p",col="black") #surprise
}

plot(0:40,seq(0,5,length=41),col="white",main="shock (just lag)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag",ii)]]$coefficients[14],type="p",col="green") #shock
  lines(ii,reglist[[paste0("haterreg.lag",ii)]]$coefficients[14],type="p",col="red") #shock
  lines(ii,reglist[[paste0("neutralreg.lag",ii)]]$coefficients[14],type="p",col="black") #shock
}

plot(0:40,seq(-3,2,length=41),col="white",main="shock (lag and contemp)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag0and",ii)]]$coefficients[17],type="p",col="green") #shock
  lines(ii,reglist[[paste0("haterreg.lag0and",ii)]]$coefficients[17],type="p",col="red") #shock
  lines(ii,reglist[[paste0("neutralreg.lag0and",ii)]]$coefficients[17],type="p",col="black") #shock
}

plot(0:40,seq(-3,3,length=41),col="white",main="shock (all lags)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_shock")],type="p",col="green") #shock
  lines(ii,reglist[[paste0("haterreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_shock")],type="p",col="red") #shock
  lines(ii,reglist[[paste0("neutralreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_shock")],type="p",col="black") #shock
}

plot(0:40,seq(0,35,length=41),col="white",main="Suspense (just lag)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag",ii)]]$coefficients[15],type="p",col="green") #suspense
  lines(ii,reglist[[paste0("haterreg.lag",ii)]]$coefficients[15],type="p",col="red") #suspense
  lines(ii,reglist[[paste0("neutralreg.lag",ii)]]$coefficients[15],type="p",col="black") #suspense
}

plot(0:40,seq(-2,35,length=41),col="white",main="Suspense (lag and contemp)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag0and",ii)]]$coefficients[18],type="p",col="green") #suspense
  lines(ii,reglist[[paste0("haterreg.lag0and",ii)]]$coefficients[18],type="p",col="red") #suspense
  lines(ii,reglist[[paste0("neutralreg.lag0and",ii)]]$coefficients[18],type="p",col="black") #suspense
}

plot(0:40,seq(-2,35,length=41),col="white",main="Suspense (all lags)")
for(ii in 0:40) {
  lines(ii,reglist[[paste0("fanreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_suspense")],type="p",col="green") #suspense
  lines(ii,reglist[[paste0("haterreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_suspense")],type="p",col="red") #suspense
  lines(ii,reglist[[paste0("neutralreg.lag0.",ii)]]$coefficients[rownames(reglist[[paste0("fanreg.lag0.",ii)]]$coefficients)==paste0("lag",ii,".sim_suspense")],type="p",col="black") #suspense
}

upperbound <- reglist$fanreg.lag0.40$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.40$coefficients))]+2*summary(reglist$fanreg.lag0.40)$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.40$coefficients)),2]
lowerbound <- reglist$fanreg.lag0.40$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.40$coefficients))]-2*summary(reglist$fanreg.lag0.40)$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.40$coefficients)),2]
plot(0:40,reglist$fanreg.lag0.40$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.40$coefficients))],
     ylim=range(upperbound,lowerbound),main="Coefficients in 40-lag fan regression for suspense",
     ylab="Coefficient",xlab="Lag length")
lines(0:40,upperbound,pch="-",type="p")
lines(0:40,lowerbound,pch="-",type="p")
for(ll in 0:40) {
  lines(rep(ll,2),c(upperbound[ll+1],lowerbound[ll+1]),lty=1)
}
abline(0,0,lty=3)

##plot for figure 7 in paper ####
upperbound.fan.suspense <- reglist$fanreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.10$coefficients))]+2*summary(reglist$fanreg.lag0.10)$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.10$coefficients)),2]
lowerbound.fan.suspense <- reglist$fanreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.10$coefficients))]-2*summary(reglist$fanreg.lag0.10)$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.10$coefficients)),2]
upperbound.fan.shock <- reglist$fanreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.10$coefficients))]+2*summary(reglist$fanreg.lag0.10)$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.10$coefficients)),2]
lowerbound.fan.shock <- reglist$fanreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.10$coefficients))]-2*summary(reglist$fanreg.lag0.10)$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.10$coefficients)),2]
upperbound.fan.surprise <- reglist$fanreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.10$coefficients))]+2*summary(reglist$fanreg.lag0.10)$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.10$coefficients)),2]
lowerbound.fan.surprise <- reglist$fanreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.10$coefficients))]-2*summary(reglist$fanreg.lag0.10)$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.10$coefficients)),2]
upperbound.hater.suspense <- reglist$haterreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.10$coefficients))]+2*summary(reglist$haterreg.lag0.10)$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.10$coefficients)),2]
lowerbound.hater.suspense <- reglist$haterreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.10$coefficients))]-2*summary(reglist$haterreg.lag0.10)$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.10$coefficients)),2]
upperbound.hater.shock <- reglist$haterreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.10$coefficients))]+2*summary(reglist$haterreg.lag0.10)$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.10$coefficients)),2]
lowerbound.hater.shock <- reglist$haterreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.10$coefficients))]-2*summary(reglist$haterreg.lag0.10)$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.10$coefficients)),2]
upperbound.hater.surprise <- reglist$haterreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.10$coefficients))]+2*summary(reglist$haterreg.lag0.10)$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.10$coefficients)),2]
lowerbound.hater.surprise <- reglist$haterreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.10$coefficients))]-2*summary(reglist$haterreg.lag0.10)$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.10$coefficients)),2]
upperbound.neutral.suspense <- reglist$neutralreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.10$coefficients))]+2*summary(reglist$neutralreg.lag0.10)$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.10$coefficients)),2]
lowerbound.neutral.suspense <- reglist$neutralreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.10$coefficients))]-2*summary(reglist$neutralreg.lag0.10)$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.10$coefficients)),2]
upperbound.neutral.shock <- reglist$neutralreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.10$coefficients))]+2*summary(reglist$neutralreg.lag0.10)$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.10$coefficients)),2]
lowerbound.neutral.shock <- reglist$neutralreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.10$coefficients))]-2*summary(reglist$neutralreg.lag0.10)$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.10$coefficients)),2]
upperbound.neutral.surprise <- reglist$neutralreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.10$coefficients))]+2*summary(reglist$neutralreg.lag0.10)$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.10$coefficients)),2]
lowerbound.neutral.surprise <- reglist$neutralreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.10$coefficients))]-2*summary(reglist$neutralreg.lag0.10)$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.10$coefficients)),2]

# jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/suspenseplots-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/suspenseshocksurpriseplots-",Sys.Date(),".jpg"),
     height=10,width=10,units = "in",res = 300)
par(mfrow=c(3,1))
# jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/surpriseplots-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
plot(0:10-0.05,reglist$fanreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.10$coefficients))],
     ylim=range(upperbound.fan.surprise,upperbound.hater.surprise,upperbound.neutral.surprise,
                lowerbound.fan.surprise,lowerbound.hater.surprise,lowerbound.neutral.surprise),
     main="Coefficients in 10-lag fan regression for surprise",type="o",col="green",
     ylab="Coefficient",xlab="Lag length")
lines(0:10-0.05,upperbound.fan.surprise,pch="-",type="p",col="green")
lines(0:10-0.05,lowerbound.fan.surprise,pch="-",type="p",col="green")
for(ll in 0:10) {
  lines(rep(ll-0.05,2),c(upperbound.fan.surprise[ll+1],lowerbound.fan.surprise[ll+1]),lty=1,col="green")
}
lines(0:10,reglist$haterreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.10$coefficients))],
      type="o",col="red")
lines(0:10,upperbound.hater.surprise,pch="-",type="p",col="red")
lines(0:10,lowerbound.hater.surprise,pch="-",type="p",col="red")
for(ll in 0:10) {
  lines(rep(ll,2),c(upperbound.hater.surprise[ll+1],lowerbound.hater.surprise[ll+1]),lty=1,col="red")
}
lines(0:10+0.05,reglist$neutralreg.lag0.10$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.10$coefficients))],
      type="o",col="black")
lines(0:10+0.05,upperbound.neutral.surprise,pch="-",type="p",col="black")
lines(0:10+0.05,lowerbound.neutral.surprise,pch="-",type="p",col="black")
for(ll in 0:10) {
  lines(rep(ll+0.05,2),c(upperbound.neutral.surprise[ll+1],lowerbound.neutral.surprise[ll+1]),lty=1,
        col="black")
}
abline(0,0,lty=3)
legend("topright",bty="n",col=c("green","red","black"),lty=1,pch=1,legend=c("fans","haters","neutral"),ncol=3)

plot(0:10-0.05,reglist$fanreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.10$coefficients))],
     ylim=range(upperbound.fan.shock,upperbound.hater.shock,upperbound.neutral.shock,
                lowerbound.fan.shock,lowerbound.hater.shock,lowerbound.neutral.shock),
     main="Coefficients in 10-lag fan regression for shock",type="o",col="green",
     ylab="Coefficient",xlab="Lag length")
lines(0:10-0.05,upperbound.fan.shock,pch="-",type="p",col="green")
lines(0:10-0.05,lowerbound.fan.shock,pch="-",type="p",col="green")
for(ll in 0:10) {
  lines(rep(ll-0.05,2),c(upperbound.fan.shock[ll+1],lowerbound.fan.shock[ll+1]),lty=1,col="green")
}
lines(0:10,reglist$haterreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.10$coefficients))],
      type="o",col="red")
lines(0:10,upperbound.hater.shock,pch="-",type="p",col="red")
lines(0:10,lowerbound.hater.shock,pch="-",type="p",col="red")
for(ll in 0:10) {
  lines(rep(ll,2),c(upperbound.hater.shock[ll+1],lowerbound.hater.shock[ll+1]),lty=1,col="red")
}
lines(0:10+0.05,reglist$neutralreg.lag0.10$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.10$coefficients))],
      type="o",col="black")
lines(0:10+0.05,upperbound.neutral.shock,pch="-",type="p",col="black")
lines(0:10+0.05,lowerbound.neutral.shock,pch="-",type="p",col="black")
for(ll in 0:10) {
  lines(rep(ll+0.05,2),c(upperbound.neutral.shock[ll+1],lowerbound.neutral.shock[ll+1]),lty=1,col="black")
}
abline(0,0,lty=3)
legend("bottomleft",bty="n",col=c("green","red","black"),lty=1,pch=1,legend=c("fans","haters","neutral"),ncol=3)

plot(0:10-0.05,reglist$fanreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.10$coefficients))],
     ylim=range(upperbound.fan.suspense,upperbound.hater.suspense,upperbound.neutral.suspense,
                lowerbound.fan.suspense,lowerbound.hater.suspense,lowerbound.neutral.suspense),
     main="Coefficients in 10-lag fan regression for suspense",type="o",
     ylab="Coefficient",xlab="Lag length",col="green")
lines(0:10-0.05,upperbound.fan.suspense,pch="-",type="p",col="green")
lines(0:10-0.05,lowerbound.fan.suspense,pch="-",type="p",col="green")
for(ll in 0:10) {
  lines(rep(ll-0.05,2),c(upperbound.fan.suspense[ll+1],lowerbound.fan.suspense[ll+1]),lty=1,col="green")
}
lines(0:10,reglist$haterreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.10$coefficients))],
      type="o",col="red")
lines(0:10,upperbound.hater.suspense,pch="-",type="p",col="red")
lines(0:10,lowerbound.hater.suspense,pch="-",type="p",col="red")
for(ll in 0:10) {
  lines(rep(ll,2),c(upperbound.hater.suspense[ll+1],lowerbound.hater.suspense[ll+1]),lty=1,col="red")
}
lines(0:10+0.05,reglist$neutralreg.lag0.10$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.10$coefficients))],
     type="o",col="black")
lines(0:10+0.05,upperbound.neutral.suspense,pch="-",type="p",col="black")
lines(0:10+0.05,lowerbound.neutral.suspense,pch="-",type="p",col="black")
for(ll in 0:10) {
  lines(rep(ll+0.05,2),c(upperbound.neutral.suspense[ll+1],lowerbound.neutral.suspense[ll+1]),lty=1,col="black")
}
abline(0,0,lty=3)
legend("topleft",bty="n",col=c("green","red","black"),lty=1,pch=1,legend=c("fans","haters","neutral"),ncol=3)

dev.off()

##plot for figure 7 (no controls) in paper ####
upperbound.nc.fan.suspense <- reglist$fanreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.nc.10$coefficients))]+2*summary(reglist$fanreg.lag0.nc.10)$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.fan.suspense <- reglist$fanreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.nc.10$coefficients))]-2*summary(reglist$fanreg.lag0.nc.10)$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.nc.10$coefficients)),2]
upperbound.nc.fan.shock <- reglist$fanreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.nc.10$coefficients))]+2*summary(reglist$fanreg.lag0.nc.10)$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.fan.shock <- reglist$fanreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.nc.10$coefficients))]-2*summary(reglist$fanreg.lag0.nc.10)$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.nc.10$coefficients)),2]
upperbound.nc.fan.surprise <- reglist$fanreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.nc.10$coefficients))]+2*summary(reglist$fanreg.lag0.nc.10)$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.fan.surprise <- reglist$fanreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.nc.10$coefficients))]-2*summary(reglist$fanreg.lag0.nc.10)$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.nc.10$coefficients)),2]
upperbound.nc.hater.suspense <- reglist$haterreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.nc.10$coefficients))]+2*summary(reglist$haterreg.lag0.nc.10)$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.hater.suspense <- reglist$haterreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.nc.10$coefficients))]-2*summary(reglist$haterreg.lag0.nc.10)$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.nc.10$coefficients)),2]
upperbound.nc.hater.shock <- reglist$haterreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.nc.10$coefficients))]+2*summary(reglist$haterreg.lag0.nc.10)$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.hater.shock <- reglist$haterreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.nc.10$coefficients))]-2*summary(reglist$haterreg.lag0.nc.10)$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.nc.10$coefficients)),2]
upperbound.nc.hater.surprise <- reglist$haterreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.nc.10$coefficients))]+2*summary(reglist$haterreg.lag0.nc.10)$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.hater.surprise <- reglist$haterreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.nc.10$coefficients))]-2*summary(reglist$haterreg.lag0.nc.10)$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.nc.10$coefficients)),2]
upperbound.nc.neutral.suspense <- reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.nc.10$coefficients))]+2*summary(reglist$neutralreg.lag0.nc.10)$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.neutral.suspense <- reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.nc.10$coefficients))]-2*summary(reglist$neutralreg.lag0.nc.10)$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.nc.10$coefficients)),2]
upperbound.nc.neutral.shock <- reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.nc.10$coefficients))]+2*summary(reglist$neutralreg.lag0.nc.10)$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.neutral.shock <- reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.nc.10$coefficients))]-2*summary(reglist$neutralreg.lag0.nc.10)$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.nc.10$coefficients)),2]
upperbound.nc.neutral.surprise <- reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.nc.10$coefficients))]+2*summary(reglist$neutralreg.lag0.nc.10)$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.nc.10$coefficients)),2]
lowerbound.nc.neutral.surprise <- reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.nc.10$coefficients))]-2*summary(reglist$neutralreg.lag0.nc.10)$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.nc.10$coefficients)),2]

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/suspenseshocksurpriseplots-nc-",Sys.Date(),".jpg"),height=10,width=10,units = "in",res = 300)
par(mfrow=c(3,1))
plot(0:10-0.05,reglist$fanreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$fanreg.lag0.nc.10$coefficients))],
     ylim=range(upperbound.nc.fan.surprise,upperbound.nc.hater.surprise,upperbound.nc.neutral.surprise,
                lowerbound.nc.fan.surprise,lowerbound.nc.hater.surprise,lowerbound.nc.neutral.surprise),
     main="Coefficients in 10-lag fan regression for surprise",type="o",col="green",
     ylab="Coefficient",xlab="Lag length")
lines(0:10-0.05,upperbound.nc.fan.surprise,pch="-",type="p",col="green")
lines(0:10-0.05,lowerbound.nc.fan.surprise,pch="-",type="p",col="green")
for(ll in 0:10) {
  lines(rep(ll-0.05,2),c(upperbound.nc.fan.surprise[ll+1],lowerbound.nc.fan.surprise[ll+1]),lty=1,col="green")
}
lines(0:10,reglist$haterreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$haterreg.lag0.nc.10$coefficients))],
      type="o",col="red")
lines(0:10,upperbound.nc.hater.surprise,pch="-",type="p",col="red")
lines(0:10,lowerbound.nc.hater.surprise,pch="-",type="p",col="red")
for(ll in 0:10) {
  lines(rep(ll,2),c(upperbound.nc.hater.surprise[ll+1],lowerbound.nc.hater.surprise[ll+1]),lty=1,col="red")
}
lines(0:10+0.05,reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_surprise",rownames(reglist$neutralreg.lag0.nc.10$coefficients))],
      type="o",col="black")
lines(0:10+0.05,upperbound.nc.neutral.surprise,pch="-",type="p",col="black")
lines(0:10+0.05,lowerbound.nc.neutral.surprise,pch="-",type="p",col="black")
for(ll in 0:10) {
  lines(rep(ll+0.05,2),c(upperbound.nc.neutral.surprise[ll+1],lowerbound.nc.neutral.surprise[ll+1]),lty=1,
        col="black")
}
abline(0,0,lty=3)
legend("topright",bty="n",col=c("green","red","black"),lty=1,pch=1,legend=c("fans","haters","neutral"),ncol=3)


plot(0:10-0.05,reglist$fanreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$fanreg.lag0.nc.10$coefficients))],
     ylim=range(upperbound.nc.fan.shock,upperbound.nc.hater.shock,upperbound.nc.neutral.shock,
                lowerbound.nc.fan.shock,lowerbound.nc.hater.shock,lowerbound.nc.neutral.shock),
     main="Coefficients in 10-lag fan regression for shock",type="o",col="green",
     ylab="Coefficient",xlab="Lag length")
lines(0:10-0.05,upperbound.nc.fan.shock,pch="-",type="p",col="green")
lines(0:10-0.05,lowerbound.nc.fan.shock,pch="-",type="p",col="green")
for(ll in 0:10) {
  lines(rep(ll-0.05,2),c(upperbound.nc.fan.shock[ll+1],lowerbound.nc.fan.shock[ll+1]),lty=1,col="green")
}
lines(0:10,reglist$haterreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$haterreg.lag0.nc.10$coefficients))],
      type="o",col="red")
lines(0:10,upperbound.nc.hater.shock,pch="-",type="p",col="red")
lines(0:10,lowerbound.nc.hater.shock,pch="-",type="p",col="red")
for(ll in 0:10) {
  lines(rep(ll,2),c(upperbound.nc.hater.shock[ll+1],lowerbound.nc.hater.shock[ll+1]),lty=1,col="red")
}
lines(0:10+0.05,reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_shock",rownames(reglist$neutralreg.lag0.nc.10$coefficients))],
      type="o",col="black")
lines(0:10+0.05,upperbound.nc.neutral.shock,pch="-",type="p",col="black")
lines(0:10+0.05,lowerbound.nc.neutral.shock,pch="-",type="p",col="black")
for(ll in 0:10) {
  lines(rep(ll+0.05,2),c(upperbound.nc.neutral.shock[ll+1],lowerbound.nc.neutral.shock[ll+1]),lty=1,col="black")
}
abline(0,0,lty=3)
legend("bottomleft",bty="n",col=c("green","red","black"),lty=1,pch=1,legend=c("fans","haters","neutral"),ncol=3)

plot(0:10-0.05,reglist$fanreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$fanreg.lag0.nc.10$coefficients))],
     ylim=range(upperbound.nc.fan.suspense,upperbound.nc.hater.suspense,upperbound.nc.neutral.suspense,
                lowerbound.nc.fan.suspense,lowerbound.nc.hater.suspense,lowerbound.nc.neutral.suspense),
     main="Coefficients in 10-lag fan regression for suspense",type="o",
     ylab="Coefficient",xlab="Lag length",col="green")
lines(0:10-0.05,upperbound.nc.fan.suspense,pch="-",type="p",col="green")
lines(0:10-0.05,lowerbound.nc.fan.suspense,pch="-",type="p",col="green")
for(ll in 0:10) {
  lines(rep(ll-0.05,2),c(upperbound.nc.fan.suspense[ll+1],lowerbound.nc.fan.suspense[ll+1]),lty=1,col="green")
}
lines(0:10,reglist$haterreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$haterreg.lag0.nc.10$coefficients))],
      type="o",col="red")
lines(0:10,upperbound.nc.hater.suspense,pch="-",type="p",col="red")
lines(0:10,lowerbound.nc.hater.suspense,pch="-",type="p",col="red")
for(ll in 0:10) {
  lines(rep(ll,2),c(upperbound.nc.hater.suspense[ll+1],lowerbound.nc.hater.suspense[ll+1]),lty=1,col="red")
}
lines(0:10+0.05,reglist$neutralreg.lag0.nc.10$coefficients[grep("sim_suspense",rownames(reglist$neutralreg.lag0.nc.10$coefficients))],
      type="o",col="black")
lines(0:10+0.05,upperbound.nc.neutral.suspense,pch="-",type="p",col="black")
lines(0:10+0.05,lowerbound.nc.neutral.suspense,pch="-",type="p",col="black")
for(ll in 0:10) {
  lines(rep(ll+0.05,2),c(upperbound.nc.neutral.suspense[ll+1],lowerbound.nc.neutral.suspense[ll+1]),lty=1,col="black")
}
abline(0,0,lty=3)
legend("topleft",bty="n",col=c("green","red","black"),lty=1,pch=1,legend=c("fans","haters","neutral"),ncol=3)
dev.off()



summary(hatermodel0.0 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home
                                 |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel0 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel1 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel2 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel3 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel4 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home +sim_surprise + sim_shock +sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel4b <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel4c <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel4d <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel4e <- lfe::felm(lhater_tweets_home ~ lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel5 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(hatermodel6 <- lfe::felm(lhater_tweets_home ~ lag1.lhater_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
stargazer::stargazer(hatermodel2,hatermodel3,hatermodel6,
  #hatermodel0.0,hatermodel0,hatermodel1,hatermodel2,hatermodel3,hatermodel4,hatermodel4c,
                     covariate.labels = c("Lagged Log Total Number of Home Tweets by Haters",
                                          "Goal","Shot","Shot hit goalframe","Corner","Yellow Card",
                                          "Red Card","Substitution","Square Difference in Probabilities",
                                          "P(Draw)","Total Goals","Goal Difference","Simulated Surprise",
                                          "Simulated Shock","Simulated Suspense","Lagged Simulated Surprise",
                                          "Lagged Simulated Shock","Lagged Simulated Suspense"))

summary(neutralmodel0.0 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home
                                   |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel0 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel1 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel2 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel3 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel4 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home +sim_surprise + sim_shock +sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel4b <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                                |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel4c <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel4d <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel4e <- lfe::felm(lneutral_tweets_home ~ lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel5 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                               |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
summary(neutralmodel6 <- lfe::felm(lneutral_tweets_home ~ lag1.lneutral_tweets_home + goal + shot + woodwork + corner + yellow + red + substitution + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff + sim_surprise + sim_shock + sim_suspense + lag1.sim_surprise + lag1.sim_shock + lag1.sim_suspense
                                 |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & is.na(data$minute)==FALSE,]))
stargazer::stargazer(neutralmodel2,neutralmodel3,neutralmodel6,
  #neutralmodel0.0,neutralmodel0,neutralmodel1,neutralmodel2,neutralmodel3,neutralmodel4,neutralmodel4c,
                     covariate.labels = c("Lagged Log Total Number of Home Tweets by Neutrals",
                                          "Goal","Shot","Shot hit goalframe","Corner","Yellow Card",
                                          "Red Card","Substitution","Square Difference in Probabilities",
                                          "P(Draw)","Total Goals","Goal Difference","Simulated Surprise",
                                          "Simulated Shock","Simulated Suspense","Lagged Simulated Surprise",
                                          "Lagged Simulated Shock","Lagged Simulated Suspense"))


summary(smodel0 <- lfe::felm(sentiment_home ~ lag1.sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(smodel1 <- lfe::felm(sentiment_home ~ lag1.sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1 + sim.sq.diff + sim_prob_draw
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(smodel2 <- lfe::felm(sentiment_home ~ lag1.sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1 + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(smodel3 <- lfe::felm(sentiment_home ~ lag1.sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1 + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(smodel4 <- lfe::felm(sentiment_home ~ lag1.sentiment_home +sim_surprise + sim_shock +sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(smodel4b <- lfe::felm(sentiment_home ~ lag1.sentiment_home + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(smodel5 <- lfe::felm(sentiment_home ~ lag1.sentiment_home + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                            |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
stargazer::stargazer(smodel0,smodel1,smodel2,smodel3,smodel4,smodel4b,smodel5,
                     covariate.labels = c("Lagged Mean Sentiment of People Tweeting with Home Team Hashtags",
                                          "Goal","Shot","Shot hit goalframe","Corner","Yellow Card",
                                          "Red Card","Substitution","Square Difference in Probabilities",
                                          "P(Draw)","Total Goals","Goal Difference","Simulated Surprise",
                                          "Simulated Shock","Simulated Suspense"))

summary(fsmodel0 <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fsmodel1 <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1 + sim.sq.diff + sim_prob_draw
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fsmodel2 <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1 + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fsmodel3 <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home + goal1 + shot1 + woodwork1 + corner1 + yellow1 + red1 + substitution1 + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fsmodel4 <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home +sim_surprise + sim_shock +sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fsmodel4b <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                              |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(fsmodel5 <- lfe::felm(fan_sentiment_home ~ lag1.fan_sentiment_home + sim.sq.diff + sim_prob_draw + totalgoals + goaldiff +sim_surprise + sim_shock +sim_suspense
                             |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
stargazer::stargazer(fsmodel0,fsmodel1,fsmodel2,fsmodel3,fsmodel4,fsmodel4b,fsmodel5,
                     covariate.labels = c("Lagged Mean Sentiment of Users Identified as Fans of Home Team",
                                          "Goal","Shot","Shot hit goalframe","Corner","Yellow Card",
                                          "Red Card","Substitution","Square Difference in Probabilities",
                                          "P(Draw)","Total Goals","Goal Difference","Simulated Surprise",
                                          "Simulated Shock","Simulated Suspense"))

data$own_sim_surprise <- - data$sim_surprise
data$own_sim_shock <- - data$sim_shock
summary(sss <- lfe::felm(lfan_tweets_away ~ lag1.lfan_tweets_away + sim_surprise + sim_shock + sim_suspense
                              |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
summary(sss2 <- lfe::felm(lfan_tweets_away ~ lag1.lfan_tweets_away + own_sim_surprise + own_sim_shock + sim_suspense
                              |Event.ID + minute,  data=data[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0,]))
stargazer::stargazer(sss,sss2)

##club specific regressions
data$selection_away[data$selection_away=="C Palace"] <- "Crystal Palace"
data$selection_home[data$selection_home=="C Palace"] <- "Crystal Palace"
teams <- unique(data$selection_home[data$selection_home!=""])
modelA <- list()
modelB <- list()
modelB2 <- list()
modelC <- list()
modelD <- list()
modelD2 <- list()
for (team in teams) {
   print(toupper(team))
   #  out <- file(paste0(fileloc,"results_by_team_eff.txt"), "a+")
   #  sink(out)

   team_data1 = data[data$selection_home==team,]
   colnames(team_data1) <- gsub("1$","_team",gsub("home","team",gsub("2$","_opp",gsub("away","opp",colnames(team_data1)))))
   team_data2 = data[data$selection_away==team,]
   colnames(team_data2) <- gsub("2$","_team",gsub("away","team",gsub("1$","_opp",gsub("home","opp",colnames(team_data1)))))
   team_data <- rbind(team_data1,team_data2)
   
   ##number of tweets
   modelA[[gsub(" ",".",selection)]] = lfe::felm(log(num_tweets_team+0.000001) ~ lag(log(num_tweets_team+0.000001)) + goal_team + shot_team + woodwork_team + corner_team + yellow_team + red_team + substitution_team + sq.diff + prob_draw + totalgoals + goaldiff + surprise + shock + suspense
                                              |Event.ID + minute,  data=team_data)
   ##number of fan tweets
   modelB[[gsub(" ",".",selection)]] = lfe::felm(log(num_retweets_team+0.000001) ~ lag(log(num_retweets_team+0.000001)) + goal_team + shot_team + woodwork_team + corner_team + yellow_team + red_team + substitution_team + sq.diff + prob_draw + totalgoals + goaldiff + surprise + shock + suspense
                                                 |Event.ID + minute,  data=team_data)
   # print(summary(modelB))
   
   modelB2[[gsub(" ",".",selection)]] = lfe::felm(sentiment_team ~ lag.sentiment_team + goal_team + shot_team + woodwork_team + corner_team + yellow_team + red_team + substitution_team + sq.diff + prob_draw + totalgoals + goaldiff + surprise + shock + suspense
                                                  |Event.ID + minute,  data=team_data)
   
   modelC[[gsub(" ",".",selection)]] = lfe::felm(log(fan_tweets_team+0.000001) ~ lag(log(fan_tweets_team+0.000001)) + goal_team + shot_team + woodwork_team + corner_team + yellow_team + red_team + substitution_team + sq.diff + prob_draw + totalgoals + goaldiff + own_surprise + own_shock + suspense
                                                 |Event.ID + minute,  data=team_data)
   # print(summary(modelC))
   
   modelD[[gsub(" ",".",selection)]] = lfe::felm(log(fan_retweets_tweet+0.000001) ~ lag(log(fan_retweets_tweet+0.000001)) + goal_team + shot_team + woodwork_team + corner_team + yellow_team + red_team + substitution_team + sq.diff + prob_draw + totalgoals + goaldiff + own_surprise + own_shock + suspense
                                                 |Event.ID + minute,  data=team_data)
   # print(summary(modelD))
   modelD2[[gsub(" ",".",selection)]] = lfe::felm(fan_sentiment_team ~ lag.fan_sentiment_team + goal_team + shot_team + woodwork_team + corner_team + yellow_team + red_team + substitution_team + sq.diff + prob_draw + totalgoals + goaldiff + own_surprise + own_shock + suspense
                                                  |Event.ID + minute,  data=team_data)
}

##lots of plots

lfct <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Sentiment Scores/epl-Liverpool-2014-04-27.csv",stringsAsFactors = FALSE)
lfc <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/team_data/2022-12-27/season_2013_agg_final_Liverpool.csv",stringsAsFactors = FALSE)
cpfc <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/team_data/2022-12-27/season_2013_agg_final_C Palace.csv",stringsAsFactors = FALSE)

data$agg_key <- as.POSIXct(data$agg_key,format="%Y-%m-%d %H:%M:%S")
lfc$agg_key <- as.POSIXct(lfc$agg_key,format="%Y-%m-%d %H:%M:%S")
cpfc$agg_key <- as.POSIXct(cpfc$agg_key,format="%Y-%m-%d %H:%M:%S")

plot(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],data$prob_home[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",ylim=range(0,1),col="purple")
lines(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],data$sim_prob_home[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",col="purple",lty=3)
lines(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],data$prob_draw[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",col=1)
lines(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],data$sim_prob_draw[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",col=1,lty=3)
lines(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],data$prob_away[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",col="red")
lines(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],data$sim_prob_away[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",col="red",lty=3)

plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],data$surprise[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l")
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],data$suspense[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l")
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],data$shock[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l")

plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$num_tweets_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="blue",
     ylim=range(c(data$num_tweets_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
                  data$num_tweets_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947])))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$num_tweets_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red")

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/cpfc-lfc-probs-2014-05-05-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$prob_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="blue",
     main="",#main="Crystal Palace 3-3 Liverpool, May 5 2014",
     ylab="P(outcome)",xlab="Timestamp",
     sub="vertical lines = goals, solid lines Betfair implied probabilities, dotted lines simulated probabilities",ylim=range(0,1))
lines(data$agg_key[data$Event.ID==27174947 & data$Inplay.flag==1],
      data$sim_prob_home[data$Event.ID==27174947 & data$Inplay.flag==1],type="l",col="blue",lty=3)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$prob_draw[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="black")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$sim_prob_draw[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="black",lty=3)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$prob_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$sim_prob_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red",lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_home)>-1],lty=1,col="grey")
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_away)>-1],lty=1,col="grey")
legend("topleft",lty=c(1,1,1),
       col=c("blue","black","red"),
       bty="n",legend=c("P(Palace win)","P(draw)","P(Liverpool win)"),ncol=1)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/cpfc-lfc-sss-2014-05-05-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$suspense[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",
     main="",#main="Crystal Palace 3-3 Liverpool, May 5 2014",
     ylab="P(outcome)",xlab="Timestamp",col="green",
     sub="vertical lines = goals, grey lines simulated",ylim=range(0,1))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$sim_suspense[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="green",lty=3)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$surprise[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="black")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$sim_surprise[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="black",lty=3)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$shock[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$sim_shock[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red",lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_home)>-1],lty=1,col="grey")
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_away)>-1],lty=1,col="grey")
legend("topleft",lty=c(rep(1,3),rep(3,3)),col=rep(c("green","black","red"),2),bty="n",legend=c("suspense","surprise","shock","sim suspense","sim surprise","sim shock"))
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/cpfc-lfc-fan-tweets-2014-05-05-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$num_tweets_total[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="black",
     main="",#main="Crystal Palace 3-3 Liverpool, May 5 2014",
     ylab="Number of Tweets",xlab="Timestamp",
     sub="vertical lines = goals",
     ylim=range(0,max(data$num_tweets_total[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947])))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$fan_tweets_total[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",lty=3)
legend("topleft",col=1,ncol = 2,
       lty=c(1:2),legend=c("All","All `fans'"),bty="n")
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/cpfc-lfc-tweets-2014-05-05-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$num_tweets_total[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="black",
     main="Crystal Palace 3-3 Liverpool, May 5 2014",
     ylab="Number of Tweets",xlab="Timestamp",
     sub="vertical lines = goals",
     ylim=range(0,max(data$num_tweets_total[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947])))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$num_tweets_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$fan_tweets_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="darkred")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$num_tweets_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="blue")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$fan_tweets_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="darkblue")
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_home)>-1],lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_away)>-1],lty=3)
legend("top",col=c("black","red","darkred","blue","darkblue"),
       lty=1,legend=c("All","All `away' tweets","Liverpool tweets","All `home' tweets","Palace tweets"),bty="n")
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/sentiment-cpfc-lfc-2014-05-05-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mfrow=c(2,1))
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",
     main="Crystal Palace 3-3 Liverpool, May 5 2014",
     ylab="Sentiment of Tweets",xlab="Timestamp",col="blue",
     sub="vertical lines = goals",
     ylim=range(c(data$sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
                  data$fan_sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
                  data$hater_sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947]),na.rm=TRUE))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$fan_sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="blue",lty=2)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$hater_sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="blue",lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_home)>-1],lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_away)>-1],lty=3)
legend("bottom",col=c("blue"),lty=1:3,ncol = 3,
       legend=c("All `home' Tweets","Palace Fan Tweets","Palace Hater Tweets"),bty="n")
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
     data$sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red",
     ylim=range(c(data$sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
                  data$fan_sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
                  data$hater_sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947]),na.rm=TRUE),
     ylab="Sentiment of Tweets",xlab="Timestamp")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$fan_sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red",lty=2)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],
      data$hater_sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947],type="l",col="red",lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_home)>-1],lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174947 & regexpr("goal",data$event_away)>-1],lty=3)
legend("bottom",col=c("red"),lty=1:3,ncol = 3,
       legend=c("All `away' Tweets","Liverpool Fan Tweets","Liverpool Hater Tweets"),bty="n")
dev.off()


plot(lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],
     lfc$fan_tweet_sent_mean_home[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],type="l",col="blue",
     main="Crystal Palace 3-3 Liverpool, May 5 2014",
     ylab="P(outcome)",xlab="Timestamp",
     sub="vertical lines = goals")
lines(lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],
      lfc$tweet_sent_mean_home[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],type="l",col="darkblue")
lines(lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],
      lfc$fan_tweet_sent_mean_away[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],type="l",col="red")
lines(lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],
      lfc$tweet_sent_mean_away[lfc$Inplay.flag==1 & lfc$Event.ID==27174947],type="l",col="darkred")
abline(v=lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174947 & regexpr("goal",lfc$event_home)>-1],lty=3)
abline(v=lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174947 & regexpr("goal",lfc$event_away)>-1],lty=3)


plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
     data$fan_sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="red",
     main="Liverpool 0-2 Chelsea, April 27 2014",
     ylab="P(outcome)",xlab="Timestamp",
     sub="vertical lines = goals",
     ylim=range(c(data$fan_sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
                  data$sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
                  data$fan_sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
                  data$sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937])))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$sentiment_home[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="darkred")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$fan_sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="blue")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$sentiment_away[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="darkblue")
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937 & regexpr("goal",data$event_home)>-1],lty=3)
abline(v=data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937 & regexpr("goal",data$event_away)>-1],lty=3)

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/lfc-cfc-sss-2014-05-05-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
     data$suspense[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="black",
     main="Liverpool 0-2 Chelsea, April 27 2014",
     ylab="P(outcome)",xlab="Timestamp",
     sub="vertical lines = goals",ylim=range(0,1))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$sim_suspense[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="grey")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$surprise[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="black",lty=2)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$sim_surprise[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",lty=2,col="grey")
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$shock[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",col="black",lty=3)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],
      data$sim_shock[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$Event.ID==27174937],type="l",lty=3,col="grey")
abline(v=lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174937 & regexpr("goal",lfc$event_home)>-1],lty=1,col="grey")
abline(v=lfc$agg_key[lfc$Inplay.flag==1 & lfc$Event.ID==27174937 & regexpr("goal",lfc$event_away)>-1],lty=1,col="grey")
legend("topleft",lty=c(1:3,1:3),col=c(rep("black",3),rep("grey",3)),bty="n",
       legend=c("suspense","surprise","shock","sim suspense","sim surprise","sim shock"))
dev.off()

plot(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$selection_home=="Arsenal" & data$selection_away=="Chelsea"],
     data$suspense[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$selection_home=="Arsenal" & data$selection_away=="Chelsea"],type="l",col="black",
     main="Arsenal 0-0 Chelsea, April 27 2014",
     ylab="P(outcome)",xlab="Timestamp",
     sub="vertical lines = goals",ylim=range(0,1))
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$selection_home=="Arsenal" & data$selection_away=="Chelsea"],
      data$surprise[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$selection_home=="Arsenal" & data$selection_away=="Chelsea"],type="l",col="black",lty=2)
lines(data$agg_key[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$selection_home=="Arsenal" & data$selection_away=="Chelsea"],
      data$shock[data$Inplay.flag==1 & data$halftime==0 & data$injurytime==0 & data$selection_home=="Arsenal" & data$selection_away=="Chelsea"],type="l",col="black",lty=3)

teamfiles <- c("season_2013_agg_final_2022-02-11_Arsenal.csv","season_2013_agg_final_2022-02-11_Aston Villa.csv",
               "season_2013_agg_final_2022-02-11_C Palace.csv","season_2013_agg_final_2022-02-11_Cardiff.csv",
               "season_2013_agg_final_2022-02-11_Chelsea.csv","season_2013_agg_final_2022-02-11_Everton.csv",
               "season_2013_agg_final_2022-02-11_Fulham.csv","season_2013_agg_final_2022-02-11_Hull.csv",
               "season_2013_agg_final_2022-02-11_Liverpool.csv","season_2013_agg_final_2022-02-11_Man City.csv",
               "season_2013_agg_final_2022-02-11_Man Utd.csv","season_2013_agg_final_2022-02-11_Newcastle.csv",
               "season_2013_agg_final_2022-02-11_Norwich.csv","season_2013_agg_final_2022-02-11_Southampton.csv",
               "season_2013_agg_final_2022-02-11_Stoke.csv","season_2013_agg_final_2022-02-11_Sunderland.csv",
               "season_2013_agg_final_2022-02-11_Swansea.csv","season_2013_agg_final_2022-02-11_Tottenham.csv",
               "season_2013_agg_final_2022-02-11_West Brom.csv","season_2013_agg_final_2022-02-11_West Ham.csv")



fav <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/favorite_teams.csv",stringsAsFactors = FALSE)
fav$fav_team[fav$fav_team==""] <- "None"
hat <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/hater_teams.csv",stringsAsFactors = FALSE)
hat$hater_team[hat$hater_team==""] <- "None"
favhat <- merge(fav,hat,by="twitter_name",all.x=TRUE)
fav.T <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/favorite_teams_tranformer.csv",stringsAsFactors = FALSE)
fav.T$fav_team[fav.T$fav_team==""] <- "None"
hat.T <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/hater_teams_tranformer.csv",stringsAsFactors = FALSE)
hat.T$hater_team[hat.T$hater_team==""] <- "None"
favhat <- merge(favhat,fav.T,by="twitter_name",all=TRUE,suffixes=c("",".T"))
favhat <- merge(favhat,hat.T,by="twitter_name",all=TRUE,suffixes=c("",".T"))
fav.B <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/favorite_teams_both.csv",stringsAsFactors = FALSE)
fav.B$fav_team[fav.B$fav_team==""] <- "None"
hat.B <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/hater_teams_both.csv",stringsAsFactors = FALSE)
hat.B$hater_team[hat.B$hater_team==""] <- "None"
favhat <- merge(favhat,fav.B,by="twitter_name",all=TRUE,suffixes=c("",".B"))
favhat <- merge(favhat,hat.B,by="twitter_name",all=TRUE,suffixes=c("",".B"))

fwb.data <- read.csv("/Users/jjreade/Dropbox/Research/Sport/Covid19 grassroots football/results-att-2013-2021.csv",stringsAsFactors = FALSE)
# fwb.data$Date <- as.Date(gsub("^(\\w+ \\d+)\\w+ (\\w+) (\\d+)$","\\1 \\2 \\3",fwb.data$date),"%A %d %B %Y")
fwb.data <- fwb.data[regexpr("^premier-league-2013-2014",fwb.data$file.name)>-1,]

twitter_followers <- data.frame(readxl::read_excel("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/Twitter follower_PL.XLSX"))
colnames(twitter_followers) <- c("Team","Followers")
twitter_followers$Team[twitter_followers$Team=="sunderland"] <- "Sunderland"

club.attendances <- aggregate(as.numeric(gsub(",","",fwb.data$attendance)),by=list(fwb.data$team1.2),FUN=mean)
favourite.teams <- data.frame(table(favhat$fav_team),stringsAsFactors = FALSE)
favourite.teams.T <- data.frame(table(favhat$fav_team.T),stringsAsFactors = FALSE)
favourite.teams.B <- data.frame(table(favhat$fav_team.B),stringsAsFactors = FALSE)
favourite.teams <- merge(favourite.teams,favourite.teams.T,by="Var1",all.x=TRUE)
favourite.teams <- merge(favourite.teams,favourite.teams.B,by="Var1",all.x=TRUE)
colnames(favourite.teams) <- c("Team","Twitter.Fans","Twitter.Fans.T","Twitter.Fans.B")
favourite.teams <- favourite.teams[favourite.teams$Team!="None",]
favourite.teams$Team <- as.character(favourite.teams$Team)
favourite.teams <- merge(favourite.teams,twitter_followers,by=c("Team"),all.x=TRUE)

favourite.teams$Team <- gsub("Tottenham","Tottenham Hotspur",gsub("West Brom","West Bromwich Albion",gsub("West Ham","West Ham United",gsub("Man City","Manchester City",gsub("Man Utd","Manchester United",gsub("Newcastle","Newcastle United",gsub("Swansea","Swansea City",gsub("Norwich","Norwich City",gsub("Stoke","Stoke City",gsub("Hull","Hull City",gsub("Cardiff","Cardiff City",gsub("C Pal","Crystal Pal",favourite.teams$Team))))))))))))
favourite.teams <- merge(favourite.teams,club.attendances,by.x="Team",by.y="Group.1",all.x=TRUE)

hated.teams <- data.frame(table(favhat$hater_team),stringsAsFactors = FALSE)
hated.teams.T <- data.frame(table(favhat$hater_team.T),stringsAsFactors = FALSE)
hated.teams.B <- data.frame(table(favhat$hater_team.B),stringsAsFactors = FALSE)
hated.teams <- merge(hated.teams,hated.teams.T,by="Var1",all.x=TRUE)
hated.teams <- merge(hated.teams,hated.teams.B,by="Var1",all.x=TRUE)
colnames(hated.teams) <- c("Team","Twitter.Haters","Twitter.Haters.T","Twitter.Haters.B")
hated.teams <- hated.teams[hated.teams$Team!="None",]
hated.teams$Team <- as.character(hated.teams$Team)

hated.teams$Team <- gsub("Tottenham","Tottenham Hotspur",gsub("West Brom","West Bromwich Albion",gsub("West Ham","West Ham United",gsub("Man City","Manchester City",gsub("Man Utd","Manchester United",gsub("Newcastle","Newcastle United",gsub("Swansea","Swansea City",gsub("Norwich","Norwich City",gsub("Stoke","Stoke City",gsub("Hull","Hull City",gsub("Cardiff","Cardiff City",gsub("C Pal","Crystal Pal",hated.teams$Team))))))))))))
favourite.teams <- merge(favourite.teams,hated.teams,by.x="Team",all.x=TRUE)

favourite.teams$team3 <- to3(favourite.teams$Team,soccerbase = FALSE)
toString(matrix(t(as.matrix(favourite.teams[,c("team3","Team")])),byrow = TRUE))

write.csv(favourite.teams,paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Datasets/favourites-and-haters",Sys.Date(),".csv"))

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-2013-2014-all-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans[favourite.teams$Team!="None"]),xaxt="n",ylab="Number of Twitter Fans/Haters (log scale)",
     xlab="",yaxt="n",ylim=range(log(c(favourite.teams$Twitter.Fans[favourite.teams$Team!="None"],
                                       favourite.teams$Twitter.Haters[favourite.teams$Team!="None"]))),
     main="",type="h",lwd=3)
lines(c(1:20-0.1),log(favourite.teams$Twitter.Fans.T[favourite.teams$Team!="None"]),type="h",col="darkgrey",lwd=3)
lines(c(1:20-0.2),log(favourite.teams$Twitter.Fans.B[favourite.teams$Team!="None"]),type="h",col="grey",lwd=3)
lines(c(1:20+0.1),log(favourite.teams$Twitter.Haters[favourite.teams$Team!="None"]),type="h",col=2,lwd=3)
lines(c(1:20+0.2),log(favourite.teams$Twitter.Haters.T[favourite.teams$Team!="None"]),type="h",col="darkred",lwd=3)
lines(c(1:20+0.3),log(favourite.teams$Twitter.Haters.B[favourite.teams$Team!="None"]),type="h",col="hotpink",lwd=3)
axis(side=1,at=1:20,labels=favourite.teams$Team[favourite.teams$Team!="None"],las=2,cex.axis=0.5)
axis(side=2,at=log(c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000)),
     labels=c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000),las=2,cex.axis=0.5)
legend("topright",col=c(1,"darkgrey","grey",2,"darkred","pink"),lwd=2,bty="n",ncol = 1,
       legend=c("Fans (RF)","Fans (BERT)","Fans (both)","Haters (RF)","Haters (BERT)","Haters (both)"),lty=1)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-2013-2014-rf-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans[favourite.teams$Team!="None"]),xaxt="n",
     ylab="Number of Twitter Fans/Haters (log scale)",
     xlab="",yaxt="n",ylim=range(log(c(favourite.teams$Twitter.Fans[favourite.teams$Team!="None"],
                                       favourite.teams$Twitter.Haters[favourite.teams$Team!="None"]))),
     main="",type="h",lwd=3)
lines(c(1:20+0.1),log(favourite.teams$Twitter.Haters[favourite.teams$Team!="None"]),type="h",col=2,lwd=3)
axis(side=1,at=1:20,labels=favourite.teams$Team[favourite.teams$Team!="None"],las=2,cex.axis=0.5)
axis(side=2,at=log(c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000)),
     labels=c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000),las=2,cex.axis=0.5)
legend("topright",col=c(1,2),lwd=2,bty="n",ncol = 1,
       legend=c("Fans","Haters"),lty=1)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-2013-2014-tf-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans.T[favourite.teams$Team!="None"]),xaxt="n",ylab="Number of Twitter Fans/Haters (log scale)",
     xlab="",yaxt="n",ylim=range(log(c(favourite.teams$Twitter.Fans.T[favourite.teams$Team!="None"],
                                       favourite.teams$Twitter.Haters.T[favourite.teams$Team!="None"]))),
     main="",type="h",lwd=3)
lines(c(1:20+0.1),log(favourite.teams$Twitter.Haters.T[favourite.teams$Team!="None"]),type="h",col=2,lwd=3)
axis(side=1,at=1:20,labels=favourite.teams$Team[favourite.teams$Team!="None"],las=2,cex.axis=0.5)
axis(side=2,at=log(c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000)),
     labels=c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000),las=2,cex.axis=0.5)
legend("topright",col=c(1,2),lwd=2,bty="n",ncol = 1,
       legend=c("Fans","Haters"),lty=1)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-2013-2014-both-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans.B[favourite.teams$Team!="None"]),xaxt="n",ylab="Number of Twitter Fans/Haters (log scale)",
     xlab="",yaxt="n",ylim=range(log(c(favourite.teams$Twitter.Fans.B[favourite.teams$Team!="None"],
                                       favourite.teams$Twitter.Haters.B[favourite.teams$Team!="None"]))),
     main="",type="h",lwd=3)
lines(c(1:20+0.1),log(favourite.teams$Twitter.Haters.B[favourite.teams$Team!="None"]),type="h",col=2,lwd=3)
axis(side=1,at=1:20,labels=favourite.teams$Team[favourite.teams$Team!="None"],las=2,cex.axis=0.5)
axis(side=2,at=log(c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000)),
     labels=c(125,250,500,1000,2000,4000,8000,16000,32000,64000,128000,256000,512000),las=2,cex.axis=0.5)
legend("topright",col=c(1,2),lwd=2,bty="n",ncol = 1,
       legend=c("Fans","Haters"),lty=1)
dev.off()

favourite.teams$team3 <- to3(favourite.teams$Team,soccerbase = FALSE)

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-scatter-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(favourite.teams$Twitter.Fans,favourite.teams$x,
     xlab="Number of Twitter Followers",ylab="Average Attendance",
     main="",xlim=range(0,max(favourite.teams$Twitter.Fans[favourite.teams$Team!="None"])+15000))
text(x ~Twitter.Fans, labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-all-log-scatter-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans),favourite.teams$x,
     xlab="Log Number of Estimated Twitter Fans",ylab="Average Attendance",
     # main="Number of Supporters of Premier League Teams in 2013/14 on Twitter",
     xlim=range(min(log(favourite.teams$Twitter.Fans.B)),max(log(favourite.teams$Twitter.Fans+80000))))
abline(lm(favourite.teams$x ~ log(favourite.teams$Twitter.Fans)))
text(x ~ log(Twitter.Fans), labels=team3,data=favourite.teams[favourite.teams$Twitter.Fans>favourite.teams$Twitter.Fans.T,], cex=0.9, font=2,pos=4)
lines(log(favourite.teams$Twitter.Fans.T),favourite.teams$x,col=2,type="p")
lines(log(favourite.teams$Twitter.Fans.B),favourite.teams$x,col=3,type="p")
text(x ~ log(Twitter.Fans.T), labels=team3,data=favourite.teams[favourite.teams$Twitter.Fans<favourite.teams$Twitter.Fans.T,], cex=0.9, font=2,pos=4)
abline(lm(favourite.teams$x ~ log(favourite.teams$Twitter.Fans.T)),col=2)
abline(lm(favourite.teams$x ~ log(favourite.teams$Twitter.Fans.B)),col=3)
# text(x ~ log(Twitter.Fans.T), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
for(tt in 1:NROW(favourite.teams)) {
  if(favourite.teams$Twitter.Fans[tt]<favourite.teams$Twitter.Fans.T[tt]) {
    lines(log(c(favourite.teams$Twitter.Fans.T[tt],favourite.teams$Twitter.Fans.B[tt])),rep(favourite.teams$x[tt],2),
          type="l",lty=3)
  } else {
    lines(log(c(favourite.teams$Twitter.Fans[tt],favourite.teams$Twitter.Fans.B[tt])),rep(favourite.teams$x[tt],2),
          type="l",lty=3)
  }
}
legend("topleft",col=1:3,pch=1,lty=3,bty="n",ncol=3,legend=c("RF","BERT","Both"))
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-rf-log-scatter-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans),favourite.teams$x,
     xlab="Log Number of Estimated Twitter Fans",ylab="Average Attendance",
     # main="Number of Supporters of Premier League Teams in 2013/14 on Twitter",
     xlim=range(min(log(favourite.teams$Twitter.Fans)),max(log(favourite.teams$Twitter.Fans+80000))))
abline(lm(favourite.teams$x ~ log(favourite.teams$Twitter.Fans)))
text(x ~ log(Twitter.Fans), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-tf-log-scatter-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans.T),favourite.teams$x,
     xlab="Log Number of Estimated Twitter Fans",ylab="Average Attendance",
     # main="Number of Supporters of Premier League Teams in 2013/14 on Twitter",
     xlim=range(min(log(favourite.teams$Twitter.Fans.T)),max(log(favourite.teams$Twitter.Fans.T+80000))))
abline(lm(favourite.teams$x ~ log(favourite.teams$Twitter.Fans.T)))
text(x ~ log(Twitter.Fans.T), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-all-log-scatter2-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans),log(1000000*favourite.teams$Followers),
     xlab="Log Number of Estimated Twitter Fans",ylab="Log Number of Actual Followers (March 2022)",
     main="",
     xlim=range(c(log(favourite.teams$Twitter.Fans),log(favourite.teams$Twitter.Fans.T),log(favourite.teams$Twitter.Fans.B))))
     # main="Number of Supporters of Premier League Teams in 2013/14 on Twitter")
abline(lm(log(1000000*favourite.teams$Followers) ~ log(favourite.teams$Twitter.Fans)))
text(log(1000000*Followers) ~ log(Twitter.Fans), labels=team3,data=favourite.teams[favourite.teams$Twitter.Fans>favourite.teams$Twitter.Fans.T,], cex=0.9, font=2,pos=4)
lines(log(favourite.teams$Twitter.Fans.T),log(1000000*favourite.teams$Followers),col=2,type="p")
lines(log(favourite.teams$Twitter.Fans.B),log(1000000*favourite.teams$Followers),col=3,type="p")
text(log(1000000*Followers) ~ log(Twitter.Fans.T), labels=team3,data=favourite.teams[favourite.teams$Twitter.Fans<favourite.teams$Twitter.Fans.T,], cex=0.9, font=2,pos=4)
abline(lm(log(1000000*favourite.teams$Followers) ~ log(favourite.teams$Twitter.Fans.T)),col=2)
abline(lm(log(1000000*favourite.teams$Followers) ~ log(favourite.teams$Twitter.Fans.B)),col=3)
# text(x ~ log(Twitter.Fans.T), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
for(tt in 1:NROW(favourite.teams)) {
  if(favourite.teams$Twitter.Fans[tt]<favourite.teams$Twitter.Fans.T[tt]) {
    lines(log(c(favourite.teams$Twitter.Fans.T[tt],favourite.teams$Twitter.Fans.B[tt])),rep(log(1000000*favourite.teams$Followers[tt]),2),
          type="l",lty=3)
  } else {
    lines(log(c(favourite.teams$Twitter.Fans[tt],favourite.teams$Twitter.Fans.B[tt])),rep(log(1000000*favourite.teams$Followers[tt]),2),
          type="l",lty=3)
  }
}
legend("topleft",col=1:3,pch=1,lty=3,bty="n",ncol=3,legend=c("RF","BERT","Both"))
# text(log(1000000*Followers) ~ log(Twitter.Fans), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-rf-log-scatter2-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans),log(1000000*favourite.teams$Followers),
     xlab="Log Number of Estimated Twitter Fans",ylab="Log Number of Actual Followers (March 2022)",
     main="")
# main="Number of Supporters of Premier League Teams in 2013/14 on Twitter")
abline(lm(log(1000000*favourite.teams$Followers) ~ log(favourite.teams$Twitter.Fans)))
text(log(1000000*Followers) ~ log(Twitter.Fans), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-bert-log-scatter2-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans.T),log(1000000*favourite.teams$Followers),
     xlab="Log Number of Estimated Twitter Fans",ylab="Log Number of Actual Followers (March 2022)",
     main="")
# main="Number of Supporters of Premier League Teams in 2013/14 on Twitter")
abline(lm(log(1000000*favourite.teams$Followers) ~ log(favourite.teams$Twitter.Fans.T)))
text(log(1000000*Followers) ~ log(Twitter.Fans.T), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/fan-distribution-both-log-scatter2-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(favourite.teams$Twitter.Fans.B),log(1000000*favourite.teams$Followers),
     xlab="Log Number of Estimated Twitter Fans",ylab="Log Number of Actual Followers (March 2022)",
     main="")
# main="Number of Supporters of Premier League Teams in 2013/14 on Twitter")
abline(lm(log(1000000*favourite.teams$Followers) ~ log(favourite.teams$Twitter.Fans.B)))
text(log(1000000*Followers) ~ log(Twitter.Fans.B), labels=team3,data=favourite.teams, cex=0.9, font=2,pos=4)
dev.off()


lfct <- merge(lfct,fav,by.x="tweeter_name",by.y="twitter_name",all.x=TRUE)

100*table(lfct$fav_team)/NROW(lfct)
100*table(lfct$fav_team[regexpr("@LFC: LOL!",lfct$tweet)>-1])/NROW(lfct$fav_team[regexpr("@LFC: LOL!",lfct$tweet)>-1])


match.summaries <- aggregate(data[,c("num_tweets_total","fan_tweets_total","hater_tweets_total","neutral_tweets_total")],
                             by=list(data$Course),FUN=sum)
match.summaries.teams.date <- data[duplicated(data$Course)==FALSE,c("Course","Date","selection_home","selection_away")]

match.summaries <- merge(match.summaries,match.summaries.teams.date,by.x=c("Group.1"),by.y=c("Course"),all.x=TRUE)

match.summaries <- match.summaries[match.summaries$num_tweets_total>0,]
match.summaries <- match.summaries[match.summaries$selection_away!="",]

match.summaries.T <- aggregate(data.T[,c("num_tweets_total","fan_tweets_total","hater_tweets_total","neutral_tweets_total")],
                             by=list(data.T$Course),FUN=sum)
match.summaries.T.teams.date <- data[duplicated(data.T$Course)==FALSE,c("Course","Date","selection_home","selection_away")]

match.summaries.T <- merge(match.summaries.T,match.summaries.T.teams.date,by.x=c("Group.1"),by.y=c("Course"),all.x=TRUE)

match.summaries.T <- match.summaries.T[match.summaries.T$num_tweets_total>0,]
match.summaries.T <- match.summaries.T[match.summaries.T$selection_away!="",]

match.summaries.B <- aggregate(data.B[,c("num_tweets_total","fan_tweets_total","hater_tweets_total","neutral_tweets_total")],
                             by=list(data.B$Course),FUN=sum)
match.summaries.B.teams.date <- data.B[duplicated(data.B$Course)==FALSE,c("Course","Date","selection_home","selection_away")]

match.summaries.B <- merge(match.summaries.B,match.summaries.B.teams.date,by.x=c("Group.1"),by.y=c("Course"),all.x=TRUE)

match.summaries.B <- match.summaries.B[match.summaries.B$num_tweets_total>0,]
match.summaries.B <- match.summaries.B[match.summaries.B$selection_away!="",]

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/tweet-numbers-rf-by-type-by-match-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(match.summaries$num_tweets_total),type="h",lwd=3,col=3,
     xaxt="n",yaxt="n",xlab="",ylab="Number of Tweets",ylim=range(0,log(max(match.summaries$num_tweets_total))),
     main="",#main="Numbers of Tweets per Match",
     sub="Black=fan, green=neutral, red=hater")
lines((log(match.summaries$fan_tweets_total+match.summaries$hater_tweets_total)),type="h",col=2,lwd=3)
lines((log(match.summaries$fan_tweets_total)),type="h",lwd=3)
axis(side = 1, at = 1:NROW(match.summaries),labels = paste0(match.summaries$selection_home," v ",match.summaries$selection_away),las=2,cex.axis=0.25)
axis(side = 2, at = log(100*2^seq(-2,11)),labels = c("25","50","100","200","400","800","1.6k","3.2k","6.4k","13k","26k","51k","102k","205k"),las=2)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/tweet-numbers-tf-by-type-by-match-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(match.summaries.T$num_tweets_total),type="h",lwd=3,col=3,
     xaxt="n",yaxt="n",xlab="",ylab="Number of Tweets",ylim=range(0,log(max(match.summaries.T$num_tweets_total))),
     main="",#main="Numbers of Tweets per Match",
     sub="Black=fan, green=neutral, red=hater")
lines((log(match.summaries.T$fan_tweets_total+match.summaries.T$hater_tweets_total)),type="h",col=2,lwd=3)
lines((log(match.summaries.T$fan_tweets_total)),type="h",lwd=3)
axis(side = 1, at = 1:NROW(match.summaries.T),labels = paste0(match.summaries.T$selection_home," v ",match.summaries.T$selection_away),las=2,cex.axis=0.25)
axis(side = 2, at = log(100*2^seq(-2,11)),labels = c("25","50","100","200","400","800","1.6k","3.2k","6.4k","13k","26k","51k","102k","205k"),las=2)
dev.off()

jpeg(paste0("/Users/jjreade/Dropbox/Research/Sport/Suprise, suspense and sentiment from Twitter/Write-up/tweet-numbers-both-by-type-by-match-",Sys.Date(),".jpg"),height=6,width=10,units = "in",res = 300)
par(mar=c(5,4,1,2) + 0.1)
plot(log(match.summaries.B$num_tweets_total),type="h",lwd=3,col=3,
     xaxt="n",yaxt="n",xlab="",ylab="Number of Tweets",ylim=range(0,log(max(match.summaries.B$num_tweets_total))),
     main="",#main="Numbers of Tweets per Match",
     sub="Black=fan, green=neutral, red=hater")
lines((log(match.summaries.B$fan_tweets_total+match.summaries.B$hater_tweets_total)),type="h",col=2,lwd=3)
lines((log(match.summaries.B$fan_tweets_total)),type="h",lwd=3)
axis(side = 1, at = 1:NROW(match.summaries.B),labels = paste0(match.summaries.B$selection_home," v ",match.summaries.B$selection_away),las=2,cex.axis=0.25)
axis(side = 2, at = log(100*2^seq(-2,11)),labels = c("25","50","100","200","400","800","1.6k","3.2k","6.4k","13k","26k","51k","102k","205k"),las=2)
dev.off()

match.summaries$fans.to.total <- match.summaries$fan_tweets_home/match.summaries$num_tweets_home
hist(match.summaries$fans.to.total,breaks=100)

match.summaries$haters.to.total <- match.summaries$hater_tweets_home/match.summaries$num_tweets_home
hist(match.summaries$haters.to.total,breaks=100)

match.summaries$neutrals.to.total <- match.summaries$neutral_tweets_home/match.summaries$num_tweets_home
hist(match.summaries$neutrals.to.total,breaks=100)
