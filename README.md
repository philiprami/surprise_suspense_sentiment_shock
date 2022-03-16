# surprise_suspense_sentiment

## PRE STEPS
commentary scrape
- output: commentary files with events
run nlp.py
- output: sentiment scores
run map_data.py
- output: json with map of sentiment files
get_fav_team.py
- output: data set with all twitter users and their favorite teams

## STEP 1
run aggregate_min.py

## STEP 2
run reformat_dataset.py

## STEP 3
run rescale.py

## STEP 4
run calculate_metrics.py

## STEP 5
run cleanup_data.py

## STEP 6 (ONLY ONCE)
run estimate_scoring_rates.py (RUN ONCE)
run get_scoring_distrib.py (RUN ONCE)
run simulate_goals.py (RUN ONCE)

## STEP 7
run calculate_suspense.py

## STEP 8
run recalculate_redcards.py

## STEP 9
run split_team_files.py
