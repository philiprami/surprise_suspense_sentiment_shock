import os
import gc
import pandas as pd
from glob import glob
import matplotlib.pyplot as plt
# pip install git+https://github.com/garrettj403/SciencePlots.git
# install latex: https://www.tug.org/mactex/mactex-download.html
plt.style.use(['science','no-latex'])
plt.rcParams.update({
    "font.family": "serif",   # specify font family here
    "font.serif": ["Times"],  # specify font here
    "font.size":11})

DATA_DIR = '../data/'
OUT_DIR = os.path.join(DATA_DIR, 'aggregated')
SIM_DIR = os.path.join(DATA_DIR, 'simulations')
DATA_DF = pd.read_csv(os.path.join(OUT_DIR, 'season_2013_complete_redcard_0909.csv'))
DISTRIBUTION = pd.read_csv(os.path.join(DATA_DIR, 'scoring_distribution.csv'), index_col=0)

# check if summary stats match table 1
sum_stats = ['mean', 'std', 'min', '50%', 'max']
emoti_cols = ['surprise_eff_prob', 'shock_eff_prob', 'suspense_eff_prob']
mask = pd.Series([True]*DATA_DF.shape[0])
for col in emoti_cols:
    mask = mask & DATA_DF[col].notnull()

print(mask.sum()) # note: 33475 observations is far less than 47,520 in the paper
DATA_DF[mask][emoti_cols].describe().T[sum_stats]

# assign minute and plot distribution
minute_goals = Counter()
DATA_DF['minute'] = None
DATA_DF['is_first_half'] = 1
for match_id, match_df in DATA_DF.groupby('Event ID'):
    starts = match_df[match_df.event_home.fillna('').str.contains('start')] # change to home
    if starts.shape[0] != 2:
        print(f'no events for match: {match_id}. skipping')
        continue
    start_index = starts.iloc[0].name
    half_index = starts.iloc[1].name
    first_half = True
    minute = 0
    for index, row in match_df.iterrows():
        if index < start_index:
            continue
        if index >= half_index:
            first_half = False
        if first_half and minute < 45:
            minute += 1
        if not first_half and minute < 91:
            minute += 1

        DATA_DF.loc[index, 'minute'] = minute
        if not first_half:
            DATA_DF.loc[index, 'is_first_half'] = 0

# plot aggregated cues
gb_surprse = DATA_DF[mask].groupby('minute')['surprise_eff_prob'].agg('mean')
gb_shock = DATA_DF[mask].groupby('minute')['shock_eff_prob'].agg('mean')
gb_suspense = DATA_DF[mask].groupby('minute')['suspense_eff_prob'].agg('mean')
gb_sent_away = DATA_DF[mask].groupby('minute')['weighted_sent_mean_away'].agg('mean')
gb_sent_home = DATA_DF[mask].groupby('minute')['weighted_sent_mean_home'].agg('mean')
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes[0, 0].step(gb_surprse.index, gb_surprse, label='surprise')
axes[0, 1].step(gb_shock.index, gb_shock, label='shock')
axes[1, 0].step(gb_suspense.index, gb_suspense, label='suspense')
axes[1, 1].step(gb_sent_away.index, gb_sent_away, label='away')
axes[1, 1].step(gb_sent_home.index, gb_sent_home, label='home')
axes[0, 0].set_title('surprise')
axes[0, 1].set_title('shock')
axes[1, 0].set_title('suspense')
axes[1, 1].set_title('sentiment')
axes[1, 1].legend(fontsize=11)
fig.savefig('../fig/agg_cues_step.png', bbox_inches='tight')
plt.show()

# plot num_tweets and tweet sentiment for sample game
random_id = np.random.choice(DATA_DF['Event ID'].unique())
sample_df = DATA_DF[DATA_DF['Event ID'] == random_id]
in_game_sample = sample_df[sample_df['minute'].notnull()]
sample_df = sample_df[sample_df['weighted_sent_mean_away'].notnull() | sample_df['weighted_sent_mean_home'].notnull()]
home_scores = in_game_sample[in_game_sample.event_home.fillna('').str.contains('goal scored')].minute
away_scores = in_game_sample[in_game_sample.event_away.fillna('').str.contains('goal scored')].minute
red_cards = in_game_sample[in_game_sample.event_away.fillna('').str.contains('red card') | in_game_sample.event_home.fillna('').str.contains('red card')].minute
fig, ax = plt.subplots(1, figsize=(12, 6))
tweet_num = in_game_sample.num_tweets_away + in_game_sample.num_tweets_home
ax.step(in_game_sample.minute, in_game_sample['weighted_sent_mean_away'], label='sentiment away', color='b')
ax.step(in_game_sample.minute, in_game_sample['weighted_sent_mean_home'], label='sentiment home', color='g')
ax2 = ax.twinx()  # instantiate a second axes that shares the same x-axis
ax2.step(in_game_sample.minute, tweet_num, label='tweet amount', color='k')
for minute in home_scores:
    plt.axvline(minute, linestyle='--', label='home score', color='g')
for minute in away_scores:
    plt.axvline(minute, linestyle='--', label='away score', color='b')
for minute in red_cards:
    plt.axvline(minute, linestyle='--', label='red card', color='r')
ax.set_ylabel('sentiment score')
ax2.set_ylabel('number of tweets')
handles, labels = ax.get_legend_handles_labels()
handles2, labels2 = ax2.get_legend_handles_labels()
by_label = dict(zip(labels+labels2, handles+handles2))
plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=11)
print(in_game_sample.Course.all())
plt.show()

fig.savefig(f'../fig/Sentiment - {sample_df.Course.all()}.png', bbox_inches='tight')


# plot suspense and goals and red cards for sample game
sus = dict(DATA_DF.groupby('Event ID').suspense_eff_prob.mean() > 0)
sus_idlist = [x for (x,y) in sus.items() if y]
mask = DATA_DF['Event ID'].isin(sus_idlist)
random_id = np.random.choice(DATA_DF[mask]['Event ID'].unique())
sample_df = DATA_DF[DATA_DF['Event ID'] == random_id]
in_game_sample = sample_df[sample_df['minute'].notnull()]
home_scores = in_game_sample[in_game_sample.event_home.fillna('').str.contains('goal scored')].minute
away_scores = in_game_sample[in_game_sample.event_away.fillna('').str.contains('goal scored')].minute
fig, ax = plt.subplots(1, figsize=(10, 5))
ax.step(in_game_sample.minute, in_game_sample['suspense_eff_prob'], label='suspense', color='b')
for minute in home_scores:
    plt.axvline(minute, linestyle='--', label='home score', color='g')
for minute in away_scores:
    plt.axvline(minute, linestyle='--', label='away score', color='b')
for minute in red_cards:
    plt.axvline(minute, linestyle='--', label='red card', color='r')
handles, labels = ax.get_legend_handles_labels()
by_label = dict(zip(labels, handles))
plt.legend(by_label.values(), by_label.keys(), fontsize=11)
print(in_game_sample.Course.all())
plt.show()

fig.savefig(f'../fig/Suspense - {sample_df.Course.all()}.png', bbox_inches='tight')

# plot scoring distribution
in_game_df = DATA_DF[DATA_DF['minute'].notnull()]
def get_goals(x):
    if pd.isnull(x):
        return 0
    count = len(re.findall('goal', x))
    return count

in_game_df['goals_home'] = in_game_df['event_home'].apply(get_goals)
in_game_df['goals_away'] = in_game_df['event_away'].apply(get_goals)
in_game_df['goals_scored'] = in_game_df['goals_home']+in_game_df['goals_away']
goal_distrib = in_game_df.groupby('minute')['goals_scored'].sum()/in_game_df['goals_scored'].sum()
goal_distrib = goal_distrib.reset_index()

fig, ax = plt.subplots(1, figsize=(10, 5))
ax.bar(goal_distrib['minute'].index, goal_distrib['goals_scored'], color='w', edgecolor='k')
ax.set_ylim(0, 0.05)
ax.set_xlim(0, 90)
plt.xlabel('minute')
plt.ylabel('density')
fig.savefig('../fig/denisty_plot.png', bbox_inches='tight')
plt.show()

# write out samples
gb = DATA_DF.groupby('Event ID')
out = pd.DataFrame()
for gbi, (match_id, match_df) in enumerate(gb):
    if gbi == 5:
        break
    else:
        out = out.append(match_df)

out.to_csv(os.path.join(OUT_DIR, '5_game_sample.csv'))

# see if the simulations converge to the empirical goal distribution
goal_counter = pd.Series([0]*DISTRIBUTION.shape[0])
simulations = glob(f'{SIM_DIR}/*')
for file_count, sim_file in enumerate(simulations):
    sim_df = pd.read_csv(sim_file, index_col=0).drop(index=['score'])
    sim_goals = sim_df.sum(axis=1)
    sim_goals.index = sim_goals.index.astype(int)
    goal_counter += sim_goals
    print('GOAL COUNTER')
    print(pd.concat([(goal_counter / goal_counter.sum()).head(10), (goal_counter / goal_counter.sum()).tail(10)]))
    print()

    print('DISTRIBUTION')
    print(DISTRIBUTION.density.tail(25))
    print(pd.concat([DISTRIBUTION.density.head(10), DISTRIBUTION.density.tail(10)]))
    print()
    print()

    del sim_df
    gc.collect()

# note: verified simulations converge to empirical distribution
