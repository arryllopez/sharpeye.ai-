"""
Smart Player Points Prediction Script
Automatically calculates rolling features from game logs
User only needs to input: Player name, Opponent, Home/Away
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

print("=" * 80)
print("SHARPEYE.AI - SMART NBA PLAYER POINTS PREDICTOR")
print("=" * 80)

# Load model and metadata
print("\n[1/4] Loading model...")
model = pickle.load(open(MODELS_DIR / "xgb_points_model.pkl", "rb"))
feature_cols = pickle.load(open(MODELS_DIR / "feature_cols.pkl", "rb"))
metadata = pickle.load(open(MODELS_DIR / "model_metadata.pkl", "rb"))
print(f"      Model loaded (MAE: {metadata['final_test_mae']:.2f} points)")

# Load game logs
print("\n[2/4] Loading game logs...")
player_logs = pd.read_csv(DATA_DIR / "raw" / "player_game_logs.csv", parse_dates=["GAME_DATE"])
team_defense = pd.read_csv(DATA_DIR / "raw" / "team_defensive_game_logs.csv", parse_dates=["GAME_DATE"])
print(f"      Loaded {len(player_logs):,} player games")
print(f"      Loaded {len(team_defense):,} team defensive games")

print("\n" + "=" * 80)
print("ENTER PREDICTION DETAILS")
print("=" * 80)

# User inputs - MINIMAL
player_name = input("\nPlayer Name: ")
opponent_team = input("Opponent Team (full name, e.g., Los Angeles Lakers): ")
is_home = input("Home game for player? (yes/no): ").lower()

is_home_value = 1 if is_home in ['yes', 'y'] else 0

print("\n[3/4] Calculating features from game logs...")

# Find player in game logs
player_data = player_logs[player_logs['PLAYER_NAME'].str.contains(player_name, case=False, na=False)]

if len(player_data) == 0:
    print(f"\nERROR: Player '{player_name}' not found in game logs!")
    print("\nAvailable players (sample):")
    print(player_logs['PLAYER_NAME'].drop_duplicates().head(20).tolist())
    exit(1)

# Get player's team
player_team = player_data.iloc[-1]['TEAM_ABBREVIATION']
print(f"      Found: {player_data.iloc[0]['PLAYER_NAME']} ({player_team})")

# Sort by date and get last 10 games
player_data = player_data.sort_values('GAME_DATE', ascending=False)
last_10_games = player_data.head(10)
last_5_games = player_data.head(5)

if len(last_10_games) < 10:
    print(f"      WARNING: Only {len(last_10_games)} games found (need 10 for best predictions)")

# Calculate rolling features
print("      Calculating player rolling stats...")

# Scoring
pts_l5 = last_5_games['PTS'].mean()
pts_l10 = last_10_games['PTS'].mean()
pts_std_l10 = last_10_games['PTS'].std()

# Minutes
min_l5 = last_5_games['MIN'].mean()
pts_per_min_l5 = pts_l5 / min_l5 if min_l5 > 0 else 0

# Usage proxy
last_5_games['USAGE_PROXY'] = last_5_games['FGA'] + 0.44 * last_5_games['FTA'] + last_5_games['TOV']
usage_l5 = last_5_games['USAGE_PROXY'].mean()

# Shooting volume
fga_l5 = last_5_games['FGA'].mean()
fg3a_l5 = last_5_games['FG3A'].mean()

# Peripherals
reb_l5 = last_5_games['REB'].mean()
ast_l5 = last_5_games['AST'].mean()
fg3m_l5 = last_5_games['FG3M'].mean()

print(f"      Player stats: {pts_l5:.1f} PPG (L5), {pts_l10:.1f} PPG (L10)")

# Get opponent defensive stats
print("      Calculating opponent defensive stats...")

# Find opponent in defense logs
opponent_defense = team_defense[team_defense['TEAM_NAME'].str.contains(opponent_team, case=False, na=False)]

if len(opponent_defense) == 0:
    print(f"\nWARNING: Opponent '{opponent_team}' not found in defensive logs!")
    print("Using league average defensive stats...")
    def_pts_allowed_l5 = 110.0
    def_3pt_allowed_l5 = 12.0
    def_3pt_pct_l5 = 0.36
else:
    # Get last 5 games
    opponent_defense = opponent_defense.sort_values('GAME_DATE', ascending=False).head(5)
    def_pts_allowed_l5 = opponent_defense['PTS_ALLOWED'].mean()
    def_3pt_allowed_l5 = opponent_defense['FG3_ALLOWED'].mean()
    def_3pt_pct_l5 = opponent_defense['OPP_FG3_PCT'].mean()

    print(f"      Opponent defense: {def_pts_allowed_l5:.1f} PPG allowed (L5)")

print("\n[4/4] Making prediction...")

# Build feature dictionary
features = {
    'IS_HOME': is_home_value,
    'PTS_L5': pts_l5,
    'PTS_L10': pts_l10,
    'PTS_STD_L10': pts_std_l10,
    'MIN_L5': min_l5,
    'PTS_PER_MIN_L5': pts_per_min_l5,
    'USAGE_L5': usage_l5,
    'FGA_L5': fga_l5,
    'FG3A_L5': fg3a_l5,
    'REB_L5': reb_l5,
    'AST_L5': ast_l5,
    'FG3M_L5': fg3m_l5,
    'DEF_PTS_ALLOWED_L5': def_pts_allowed_l5,
    'DEF_3PT_ALLOWED_L5': def_3pt_allowed_l5,
    'DEF_3PT_PCT_L5': def_3pt_pct_l5,
}

# Add team categorical features
for col in feature_cols:
    if col not in features:
        features[col] = 0

# Set player's team
team_col = f"TEAM_ABBREVIATION_{player_team}"
if team_col in feature_cols:
    features[team_col] = 1

# Set opponent team
opp_col = f"OPP_TEAM_NAME_{opponent_team}"
if opp_col in feature_cols:
    features[opp_col] = 1

# Create prediction DataFrame
X = pd.DataFrame([features])[feature_cols]

print("\n" + "=" * 80)
print("PREDICTION RESULTS")
print("=" * 80)

# Predict
predicted_points = model.predict(X)[0]

print(f"\nPlayer: {player_data.iloc[0]['PLAYER_NAME']}")
print(f"Team: {player_team}")
print(f"Opponent: {opponent_team}")
print(f"Location: {'HOME' if is_home_value == 1 else 'AWAY'}")
print(f"\n{'='*80}")
print(f"PREDICTED POINTS: {predicted_points:.1f}")
print(f"{'='*80}")

# Recent performance context
print(f"\nRecent Performance:")
print(f"  Last 5 games avg:  {pts_l5:.1f} PPG")
print(f"  Last 10 games avg: {pts_l10:.1f} PPG")
print(f"  Consistency (std): {pts_std_l10:.1f} points")
print(f"  Minutes per game:  {min_l5:.1f}")

print(f"\nOpponent Defense:")
print(f"  Points allowed:    {def_pts_allowed_l5:.1f} PPG")
print(f"  Defense quality:   {'Weak' if def_pts_allowed_l5 > 115 else 'Strong' if def_pts_allowed_l5 < 105 else 'Average'}")

# Model quality
print("\n" + "=" * 80)
print("MODEL QUALITY")
print("=" * 80)

if pts_std_l10 < 4:
    consistency = "VERY CONSISTENT (low variance)"
elif pts_std_l10 < 6:
    consistency = "CONSISTENT (moderate variance)"
else:
    consistency = "VOLATILE (high variance)"

print(f"\nPlayer Consistency: {consistency}")
print(f"Model MAE: {metadata['final_test_mae']:.2f} points")
print(f"Model Stability: {metadata['cv_coefficient_of_variation']:.1f}% CV")
print(f"Validation Games: {metadata['test_size']:,}")

print("\n" + "=" * 80 + "\n")
print("Thanks for using SharpEye.AI!")
