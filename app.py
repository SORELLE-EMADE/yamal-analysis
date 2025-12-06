import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mplsoccer import Pitch
from statsbombpy import sb

# ---------------------------------------------------------------------
# Page config to remove "Deploy" and three dots
# ---------------------------------------------------------------------
st.set_page_config(page_title="Lamine Yamal Analysis", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

# ---------------------------------------------------------------------
# Title
# ---------------------------------------------------------------------
st.title("Analysis and Comparison of Lamine Yamal – Euro 2024")

# ---------------------------------------------------------------------
# Match selection (showing team names)
# ---------------------------------------------------------------------
competition_id = 55  # Euro 2024
season_id = 282
matches = sb.matches(competition_id=competition_id, season_id=season_id)
spain_matches = matches[(matches['home_team']=='Spain') | (matches['away_team']=='Spain')]

# Create a label combining home and away teams
spain_matches['match_label'] = spain_matches['home_team'] + " vs " + spain_matches['away_team']

# Let user select by team names
match_choice_label = st.selectbox("Select a match:", spain_matches['match_label'])

# Get corresponding match_id
match_choice = spain_matches[spain_matches['match_label']==match_choice_label]['match_id'].values[0]

events = sb.events(match_id=int(match_choice))

# ---------------------------------------------------------------------
# Extraction of Yamal actions
# ---------------------------------------------------------------------
yamal = events[events['player'].str.contains("Lamine", na=False)]

def extract_xy(loc):
    if isinstance(loc, list) and len(loc) == 2:
        return loc[0], loc[1]
    return None, None

# Filter by action type
dribbles = yamal[yamal['type']=='Dribble'].copy()
passes = yamal[yamal['type']=='Pass'].copy()
shots = yamal[yamal['type']=='Shot'].copy()

# Extract coordinates
for df in [dribbles, passes, shots]:
    df['x'], df['y'] = zip(*df['location'].apply(extract_xy))

# ---------------------------------------------------------------------
# Summary statistics for all players
# ---------------------------------------------------------------------
players = events['player'].dropna().unique()
summary = []

for p in players:
    pe = events[events['player']==p]
    
    d = pe[pe['type']=='Dribble']
    d_succ = d[d['location'].apply(lambda l: isinstance(l, list) and l[0] > 60)]
    
    pa = pe[pe['type']=='Pass']
    pa_s = pa[pa['pass_outcome'].isna()]
    
    sh = pe[pe['type']=='Shot']
    sh_s = sh[sh['shot_outcome'].isin(['Goal','Saved','Post'])]
    
    summary.append({
        'player': p,
        'dribbles_success': len(d_succ),
        'passes_success': len(pa_s),
        'shots_on_target': len(sh_s)
    })

summary_df = pd.DataFrame(summary).sort_values(by='dribbles_success', ascending=False)

# ---------------------------------------------------------------------
# Player selection for comparison
# ---------------------------------------------------------------------
try:
    yamal_index = int(summary_df[summary_df['player'].str.contains("Lamine",na=False)].index[0])
except:
    yamal_index = 0

player_name = st.selectbox("Compare with:", summary_df['player'], index=yamal_index)

st.subheader(f"Statistics of {player_name}")
player_stats = summary_df[summary_df['player']==player_name]
st.write(player_stats)

# ---------------------------------------------------------------------
# Visual comparison – Top 10
# ---------------------------------------------------------------------
st.subheader("Top 10 – Comparison of successful dribbles, passes, and shots on target")

top10 = summary_df.head(10)
plt.figure(figsize=(10,5))

x = range(len(top10))
plt.bar(x, top10['dribbles_success'], label='Successful dribbles')
plt.bar([i+0.3 for i in x], top10['passes_success'], label='Successful passes')
plt.bar([i+0.6 for i in x], top10['shots_on_target'], label='Shots on target')

plt.xticks([i+0.3 for i in x], top10['player'], rotation=45, ha='right')
plt.ylabel("Count")
plt.legend()
st.pyplot(plt)

# ---------------------------------------------------------------------
# Yamal actions on the pitch
# ---------------------------------------------------------------------
st.subheader("Pitch map of Lamine Yamal actions")

pitch = Pitch(pitch_type='statsbomb')
fig, ax = pitch.draw(figsize=(10,6))

# Plot Dribbles
ax.scatter(dribbles['x'], dribbles['y'], s=100, c='blue', edgecolors='black', label='Dribbles')
# Plot Passes
ax.scatter(passes['x'], passes['y'], s=100, c='green', edgecolors='black', label='Passes')
# Plot Shots
ax.scatter(shots['x'], shots['y'], s=160, c='orange', edgecolors='black', label='Shots')

ax.legend(loc='upper right')
st.pyplot(fig)
