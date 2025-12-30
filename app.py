# =====================================================
# IMPORTS
# =====================================================
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from mplsoccer import Pitch
from statsbombpy import sb
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
import os

# =====================================================
# STREAMLIT CONFIG
# =====================================================
st.set_page_config(
    page_title="Lamine Yamal Analysis – Euro 2024",
    page_icon="⚽",
    layout="wide"
)

st.title("Analysis and Comparison of Lamine Yamal – Euro 2024")

# =====================================================
# MATCH SELECTION
# =====================================================
competition_id = 55  # Euro 2024
season_id = 282

matches = sb.matches(competition_id=competition_id, season_id=season_id)
spain_matches = matches[
    (matches['home_team'] == 'Spain') | (matches['away_team'] == 'Spain')
].copy()

spain_matches['match_label'] = (
    spain_matches['home_team'] + " vs " + spain_matches['away_team']
)

match_choice_label = st.selectbox(
    "Select a match:",
    spain_matches['match_label']
)

match_id = spain_matches.loc[
    spain_matches['match_label'] == match_choice_label, 'match_id'
].values[0]

events = sb.events(match_id=int(match_id))

# =====================================================
# FILTER LAMINE YAMAL ACTIONS
# =====================================================
yamal = events[events['player'].str.contains("Lamine", na=False)].copy()

def extract_xy(loc):
    if isinstance(loc, list) and len(loc) == 2:
        return loc[0], loc[1]
    return None, None

# Main actions
passes = yamal[yamal['type'] == 'Pass'].copy()
shots = yamal[yamal['type'] == 'Shot'].copy()
carries = yamal[yamal['type'] == 'Carry'].copy()

for df in [passes, shots, carries]:
    df['x'], df['y'] = zip(*df['location'].apply(extract_xy))

# =====================================================
# SUMMARY STATS FOR ALL PLAYERS
# =====================================================
players = events['player'].dropna().unique()
summary = []

for p in players:
    pe = events[events['player'] == p]

    prog_carries = pe[
        (pe['type'] == 'Carry') &
        (pe['location'].apply(lambda x: isinstance(x, list) and x[0] >= 60))
    ]

    final_passes = pe[
        (pe['type'] == 'Pass') &
        (pe['location'].apply(lambda x: isinstance(x, list) and x[0] >= 80))
    ]

    shots_ot = pe[
        (pe['type'] == 'Shot') &
        (pe['shot_outcome'].isin(['Goal', 'Saved', 'Post']))
    ]

    summary.append({
        'player': p,
        'progressive_carries': len(prog_carries),
        'final_third_passes': len(final_passes),
        'shots': len(shots_ot)
    })

stats_df = pd.DataFrame(summary)

# =====================================================
# PLAYER COMPARISON TABLE
# =====================================================
try:
    yamal_index = int(
        stats_df[stats_df['player'].str.contains("Lamine", na=False)].index[0]
    )
except:
    yamal_index = 0

player_choice = st.selectbox(
    "Compare Lamine Yamal with:",
    stats_df['player'],
    index=yamal_index
)

st.subheader(f"Statistics – {player_choice}")
st.dataframe(stats_df[stats_df['player'] == player_choice])

# =====================================================
# FIGURE 2 – BAR PLOT COMPARISON
# =====================================================
st.subheader("Figure 2 – Comparison of key attacking metrics")

top_carries = stats_df.sort_values(
    by='progressive_carries', ascending=False
).head(6)

top_passes = stats_df.sort_values(
    by='final_third_passes', ascending=False
).head(6)

top_shots = stats_df.sort_values(
    by='shots', ascending=False
).head(6)

players_combined = list(
    set(top_carries['player']) |
    set(top_passes['player']) |
    set(top_shots['player'])
)
players_combined.sort()

carries_vals = [
    stats_df.loc[stats_df['player'] == p, 'progressive_carries'].values[0]
    for p in players_combined
]
passes_vals = [
    stats_df.loc[stats_df['player'] == p, 'final_third_passes'].values[0]
    for p in players_combined
]
shots_vals = [
    stats_df.loc[stats_df['player'] == p, 'shots'].values[0]
    for p in players_combined
]

x = np.arange(len(players_combined))
width = 0.25

fig2, ax2 = plt.subplots(figsize=(10, 6))

ax2.bar(x - width, carries_vals, width,
        color='#1E88E5', label='Progressive carries')
ax2.bar(x, passes_vals, width,
        color='#C0CA33', label='Final third passes')
ax2.bar(x + width, shots_vals, width,
        color='#FB8C00', label='Shots')

ax2.set_ylabel("Number of actions")
ax2.set_xlabel("Players")
ax2.set_title("Comparison of key attacking metrics – Euro 2024")
ax2.set_xticks(x)
ax2.set_xticklabels(players_combined, rotation=45)
ax2.legend()

st.pyplot(fig2)

# =====================================================
# FIGURE 1 – PITCH MAP (STYLE PRO)
# =====================================================
st.subheader("Figure 1 – Lamine Yamal attacking impact")

os.makedirs("figures", exist_ok=True)

pitch = Pitch(
    pitch_type='statsbomb',
    pitch_color='#2E7D32',
    line_color='white'
)

fig1, ax1 = pitch.draw(figsize=(10, 7))

# Highlight right flank
ax1.add_patch(Rectangle(
    (0, 0), 120, 40,
    facecolor='#66BB6A',
    alpha=0.25,
    zorder=0
))

# Highlight final third
ax1.add_patch(Rectangle(
    (80, 0), 40, 80,
    facecolor='#81C784',
    alpha=0.25,
    zorder=0
))

# Progressive carries arrows
for _, row in carries.iterrows():
    if isinstance(row.get('carry_end_location'), list):
        pitch.arrows(
            row['location'][0], row['location'][1],
            row['carry_end_location'][0], row['carry_end_location'][1],
            ax=ax1,
            width=2,
            headwidth=6,
            headlength=6,
            color='#1E88E5',
            alpha=0.9
        )

# Final third passes
final_third_passes = passes[passes['x'] >= 80]
for _, row in final_third_passes.iterrows():
    if isinstance(row.get('pass_end_location'), list):
        pitch.lines(
            row['location'][0], row['location'][1],
            row['pass_end_location'][0], row['pass_end_location'][1],
            ax=ax1,
            lw=1.2,
            color='#C0CA33',
            alpha=0.5
        )

# Shots
pitch.scatter(
    shots['x'], shots['y'],
    ax=ax1,
    s=160,
    color='#FB8C00',
    edgecolors='black'
)

legend_elements = [
    Line2D([0], [0], color='#1E88E5', lw=2, label='Progressive carries'),
    Line2D([0], [0], color='#C0CA33', lw=2, label='Final third passes'),
    Line2D([0], [0], marker='o', color='w', label='Shots',
           markerfacecolor='#FB8C00',
           markeredgecolor='black', markersize=10),
    Line2D([0], [0], color='#66BB6A', lw=6,
           alpha=0.6, label='Key attacking zones')
]

ax1.legend(
    handles=legend_elements,
    loc='upper left',
    frameon=True,
    facecolor='white'
)

ax1.set_title(
    "Lamine Yamal – Attacking impact on the right flank\nEuro 2024",
    fontsize=14,
    color='white',
    pad=15
)

st.pyplot(fig1)
