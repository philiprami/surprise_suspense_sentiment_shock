# surprise_suspense_sentiment

## PRE STEP 1

add sentiment scores with nlp.py

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

## STEP 6

run estimate_scoring_rates.py
run get_scoring_distrib.py
run simulate_goals.py
  runs simulate_goals_solo.py

## TO DO
* calculate suspense
* event takes place after end
* first half wrong in lots of games. random active flags are messing it up
  remove active flags before game start
* redo sentiment model

# suspense
* join in red card events
* scorelines are recorded of each of the simulation
* iterate through every minute
  * at each minute given the current score
    each minute uses a little bit of real time data (current score) and the rest is simulated
    given current score, in the given minute... simulate the rest of the match 100,000 times
  * also record whether there's a goal in the next minute
  * will be a subset in the simulations where this is the case

* use
