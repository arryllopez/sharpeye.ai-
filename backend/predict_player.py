"""
Smart Player Points Prediction Script
Automatically calculates rolling features from game logs
Includes: Pace features, Positional defense, Team features
"""

import pickle
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Team mapping
TEAM_ABBR_TO_NAME = {
    "ATL": "Atlanta Hawks", "BOS": "Boston Celtics", "BKN": "Brooklyn Nets",
    "CHA": "Charlotte Hornets", "CHI": "Chicago Bulls", "CLE": "Cleveland Cavaliers",
    "DAL": "Dallas Mavericks", "DEN": "Denver Nuggets", "DET": "Detroit Pistons",
    "GSW": "Golden State Warriors", "HOU": "Houston Rockets", "IND": "Indiana Pacers",
    "LAC": "LA Clippers", "LAL": "Los Angeles Lakers", "MEM": "Memphis Grizzlies",
    "MIA": "Miami Heat", "MIL": "Milwaukee Bucks", "MIN": "Minnesota Timberwolves",
    "NOP": "New Orleans Pelicans", "NYK": "New York Knicks", "OKC": "Oklahoma City Thunder",
    "ORL": "Orlando Magic", "PHI": "Philadelphia 76ers", "PHX": "Phoenix Suns",
    "POR": "Portland Trail Blazers", "SAC": "Sacramento Kings", "SAS": "San Antonio Spurs",
    "TOR": "Toronto Raptors", "UTA": "Utah Jazz", "WAS": "Washington Wizards",
}

# Paths
BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATA_DIR = BASE_DIR / "data"

print("=" * 80)
print("SHARPEYE.AI - NBA PLAYER POINTS PREDICTOR (WITH PACE & POSITIONAL DEFENSE)")
print("=" * 80)

# Load model and metadata
print("\n[1/5] Loading model...")
model = pickle.load(open(MODELS_DIR / "xgb_points_model.pkl", "rb"))
feature_cols = pickle.load(open(MODELS_DIR / "feature_cols.pkl", "rb"))
metadata = pickle.load(open(MODELS_DIR / "model_metadata.pkl", "rb"))
print(f"      Model loaded (CV MAE: {metadata['cv_mean_mae']:.2f} ± {metadata['cv_std_mae']:.2f} points)")

# Load game logs
print("\n[2/5] Loading game logs...")
player_logs = pd.read_csv(DATA_DIR / "raw" / "player_game_logs.csv", parse_dates=["GAME_DATE"])
team_defense = pd.read_csv(DATA_DIR / "raw" / "team_defensive_game_logs.csv", parse_dates=["GAME_DATE"])
print(f"      Loaded {len(player_logs):,} player games")
print(f"      Loaded {len(team_defense):,} team defensive games")

print("\n" + "=" * 80)
print("ENTER PREDICTION DETAILS")
print("=" * 80)

# User inputs
player_name = input("\nPlayer Name: ")
opponent_team = input("Opponent Team (full name, e.g., Los Angeles Lakers): ")
is_home = input("Home game for player? (yes/no): ").lower()
game_date_str = input("Game Date (YYYY-MM-DD, or press Enter for today): ").strip()

# Parse game date
if not game_date_str:
    game_date = pd.Timestamp.now()
    print(f"      Using today's date: {game_date.date()}")
else:
    try:
        game_date = pd.to_datetime(game_date_str)
        print(f"      Using date: {game_date.date()}")
    except:
        print(f"      Invalid date format, using today")
        game_date = pd.Timestamp.now()

is_home_value = 1 if is_home in ['yes', 'y'] else 0

print("\n[3/5] Calculating player features from game logs...")

# Find player in game logs
player_data = player_logs[player_logs['PLAYER_NAME'].str.contains(player_name, case=False, na=False)]

if len(player_data) == 0:
    print(f"\nERROR: Player '{player_name}' not found in game logs!")
    print("\nAvailable players (sample):")
    print(player_logs['PLAYER_NAME'].drop_duplicates().head(20).tolist())
    exit(1)

# Get player info
player_full_name = player_data.iloc[0]['PLAYER_NAME']
player_team = player_data.iloc[-1]['TEAM_ABBREVIATION']
player_position = player_data.iloc[-1]['POSITION'] if 'POSITION' in player_data.columns else 'Unknown'

print(f"      Found: {player_full_name} ({player_team}, {player_position})")

# Get games BEFORE the prediction date (to avoid lookahead)
historical_games = player_data[player_data['GAME_DATE'] < game_date].sort_values('GAME_DATE', ascending=False)

if len(historical_games) < 10:
    print(f"      WARNING: Only {len(historical_games)} historical games found before {game_date.date()}")
    print(f"      Need at least 10 games for accurate predictions!")

last_10_games = historical_games.head(10)
last_5_games = historical_games.head(5)

# Calculate rolling features
print("      Calculating player rolling stats...")

# Scoring
pts_l5 = last_5_games['PTS'].mean()
pts_l10 = last_10_games['PTS'].mean()
pts_std_l10 = last_10_games['PTS'].std()

# Minutes
min_l5 = last_5_games['MIN'].mean()
min_l10 = last_10_games['MIN'].mean()
pts_per_min_l5 = pts_l5 / min_l5 if min_l5 > 0 else 0

# Usage proxy
last_5_games_copy = last_5_games.copy()
last_5_games_copy['USAGE_PROXY'] = last_5_games_copy['FGA'] + 0.44 * last_5_games_copy['FTA'] + last_5_games_copy['TOV']
usage_l5 = last_5_games_copy['USAGE_PROXY'].mean()

# Shooting volume
fga_l5 = last_5_games['FGA'].mean()
fg3a_l5 = last_5_games['FG3A'].mean()

# Peripherals
reb_l5 = last_5_games['REB'].mean()
ast_l5 = last_5_games['AST'].mean()
fg3m_l5 = last_5_games['FG3M'].mean()

# Rest Days - days since last game
if len(historical_games) > 1:
    rest_days = (game_date - historical_games.iloc[0]['GAME_DATE']).days
else:
    rest_days = 2

print(f"      Player stats: {pts_l5:.1f} PPG (L5), {pts_l10:.1f} PPG (L10)")
print(f"      Minutes: {min_l5:.1f} MPG (L5), Rest: {rest_days} day(s)")

# Get opponent defensive stats
print("\n[4/5] Calculating opponent features...")

# Find opponent in defense logs (games BEFORE prediction date)
opponent_defense = team_defense[
    (team_defense['TEAM_NAME'].str.contains(opponent_team, case=False, na=False)) &
    (team_defense['GAME_DATE'] < game_date)
].sort_values('GAME_DATE', ascending=False)

if len(opponent_defense) == 0:
    print(f"      WARNING: Opponent '{opponent_team}' not found in defensive logs!")
    print("      Using league average stats...")
    def_pts_allowed_l5 = 110.0
    def_3pt_allowed_l5 = 12.0
    def_3pt_pct_l5 = 0.36
    opp_pace_l5 = 100.0
    opp_pace_l10 = 100.0
    def_pts_vs_position_l5 = 55.0
    def_pts_vs_position_l10 = 55.0
else:
    # Get last 5 and 10 games for opponent
    opp_last_5 = opponent_defense.head(5)
    opp_last_10 = opponent_defense.head(10)

    def_pts_allowed_l5 = opp_last_5['PTS_ALLOWED'].mean()
    def_3pt_allowed_l5 = opp_last_5['FG3_ALLOWED'].mean()
    def_3pt_pct_l5 = opp_last_5['OPP_FG3_PCT'].mean()
    opp_pace_l5 = opp_last_5['GAME_PACE'].mean() if 'GAME_PACE' in opp_last_5.columns else 100.0
    opp_pace_l10 = opp_last_10['GAME_PACE'].mean() if 'GAME_PACE' in opp_last_10.columns else 100.0

    print(f"      Opponent defense: {def_pts_allowed_l5:.1f} PPG allowed (L5)")
    print(f"      Opponent pace: {opp_pace_l5:.1f} possessions/game (L5)")

    # Calculate positional defense
    # Get all player games against this opponent before prediction date
    raw_player_logs = pd.read_csv(DATA_DIR / "raw" / "player_game_logs.csv", parse_dates=["GAME_DATE"])

    # Find games where this opponent was playing (extract opponent from matchup)
    def extract_opponent(matchup):
        if "vs." in matchup:
            return matchup.split("vs.")[-1].strip()
        if "@" in matchup:
            return matchup.split("@")[-1].strip()
        return None

    raw_player_logs['OPP_ABBR'] = raw_player_logs['MATCHUP'].apply(extract_opponent)

    # Find the opponent's abbreviation
    opponent_abbr = None
    for abbr, full_name in TEAM_ABBR_TO_NAME.items():
        if full_name.lower() == opponent_team.lower():
            opponent_abbr = abbr
            break

    if opponent_abbr and player_position in ['Guard', 'Forward', 'Center']:
        # Get games where players of this position played against this opponent
        position_games = raw_player_logs[
            (raw_player_logs['OPP_ABBR'] == opponent_abbr) &
            (raw_player_logs['POSITION'] == player_position) &
            (raw_player_logs['GAME_DATE'] < game_date)
        ].sort_values('GAME_DATE', ascending=False)

        if len(position_games) >= 5:
            # Aggregate points by game date
            position_pts_by_game = position_games.groupby('GAME_DATE')['PTS'].sum().reset_index()
            position_pts_by_game = position_pts_by_game.sort_values('GAME_DATE', ascending=False)

            def_pts_vs_position_l5 = position_pts_by_game.head(5)['PTS'].mean()
            def_pts_vs_position_l10 = position_pts_by_game.head(10)['PTS'].mean() if len(position_pts_by_game) >= 10 else def_pts_vs_position_l5

            print(f"      Opponent allows {def_pts_vs_position_l5:.1f} PPG to {player_position}s (L5)")
        else:
            def_pts_vs_position_l5 = 55.0
            def_pts_vs_position_l10 = 55.0
            print(f"      Not enough positional data, using defaults")
    else:
        def_pts_vs_position_l5 = 55.0
        def_pts_vs_position_l10 = 55.0

# Get player's team pace
print("      Calculating player's team pace...")

player_team_full = TEAM_ABBR_TO_NAME.get(player_team, None)

if player_team_full:
    player_team_defense = team_defense[
        (team_defense['TEAM_NAME'] == player_team_full) &
        (team_defense['GAME_DATE'] < game_date)
    ].sort_values('GAME_DATE', ascending=False)

    if len(player_team_defense) >= 5:
        player_team_last_5 = player_team_defense.head(5)
        player_team_last_10 = player_team_defense.head(10)

        player_team_pace_l5 = player_team_last_5['GAME_PACE'].mean() if 'GAME_PACE' in player_team_last_5.columns else 100.0
        player_team_pace_l10 = player_team_last_10['GAME_PACE'].mean() if 'GAME_PACE' in player_team_last_10.columns else 100.0

        print(f"      Player's team pace: {player_team_pace_l5:.1f} possessions/game (L5)")
    else:
        player_team_pace_l5 = 100.0
        player_team_pace_l10 = 100.0
        print(f"      Not enough team data, using defaults")
else:
    player_team_pace_l5 = 100.0
    player_team_pace_l10 = 100.0

# Calculate expected game pace and possessions
expected_game_pace_l5 = (player_team_pace_l5 + opp_pace_l5) / 2.0
expected_game_pace_l10 = (player_team_pace_l10 + opp_pace_l10) / 2.0

expected_possessions_l5 = (min_l5 / 48.0) * expected_game_pace_l5
expected_possessions_l10 = (min_l10 / 48.0) * expected_game_pace_l10

print(f"      Expected game pace: {expected_game_pace_l5:.1f} possessions")
print(f"      Expected player possessions: {expected_possessions_l5:.1f}")

print("\n[5/5] Making prediction...")

# Build feature dictionary with ALL features
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
    'REST_DAYS': rest_days,
    'DEF_PTS_ALLOWED_L5': def_pts_allowed_l5,
    'DEF_3PT_ALLOWED_L5': def_3pt_allowed_l5,
    'DEF_3PT_PCT_L5': def_3pt_pct_l5,
    'DEF_PTS_VS_POSITION_L5': def_pts_vs_position_l5,
    'DEF_PTS_VS_POSITION_L10': def_pts_vs_position_l10,
    'PLAYER_TEAM_PACE_L5': player_team_pace_l5,
    'PLAYER_TEAM_PACE_L10': player_team_pace_l10,
    'OPP_PACE_L5': opp_pace_l5,
    'OPP_PACE_L10': opp_pace_l10,
    'EXPECTED_GAME_PACE_L5': expected_game_pace_l5,
    'EXPECTED_GAME_PACE_L10': expected_game_pace_l10,
    'EXPECTED_POSSESSIONS_L5': expected_possessions_l5,
    'EXPECTED_POSSESSIONS_L10': expected_possessions_l10,
}

# Add team categorical features (one-hot encoding)
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

# Verify no missing features
missing_features = [col for col in feature_cols if col not in features]
if missing_features:
    print(f"\n      WARNING: {len(missing_features)} features missing:")
    for feat in missing_features[:5]:
        print(f"        - {feat}")

print("\n" + "=" * 80)
print("PREDICTION RESULTS")
print("=" * 80)

# Predict
predicted_points = model.predict(X)[0]

print(f"\nPlayer: {player_full_name}")
print(f"Position: {player_position}")
print(f"Team: {player_team}")
print(f"Opponent: {opponent_team}")
print(f"Location: {'HOME' if is_home_value == 1 else 'AWAY'}")
print(f"Game Date: {game_date.date()}")
print(f"\n{'='*80}")
print(f"PREDICTED POINTS: {predicted_points:.1f}")
print(f"{'='*80}")

# Recent performance context
print(f"\nRecent Performance:")
print(f"  Last 5 games avg:  {pts_l5:.1f} PPG")
print(f"  Last 10 games avg: {pts_l10:.1f} PPG")
print(f"  Consistency (std): {pts_std_l10:.1f} points")
print(f"  Minutes per game:  {min_l5:.1f} MPG")
print(f"  Expected possessions: {expected_possessions_l5:.1f}")

print(f"\nMatchup Analysis:")
print(f"  Opponent defense:     {def_pts_allowed_l5:.1f} PPG allowed")
print(f"  Defense vs {player_position}s: {def_pts_vs_position_l5:.1f} PPG allowed")
print(f"  Defense quality:      {'Weak' if def_pts_allowed_l5 > 115 else 'Strong' if def_pts_allowed_l5 < 105 else 'Average'}")

print(f"\nPace Context:")
print(f"  {player_team} pace:      {player_team_pace_l5:.1f} possessions/game")
print(f"  {opponent_team[:20]} pace: {opp_pace_l5:.1f} possessions/game")
print(f"  Expected game pace:  {expected_game_pace_l5:.1f} possessions/game")
print(f"  Pace environment:    {'Fast' if expected_game_pace_l5 > 102 else 'Slow' if expected_game_pace_l5 < 98 else 'Average'}")

# Prediction interval (90%)
monte_carlo_std = metadata['monte_carlo']['recommended_std']
lower_90 = predicted_points + metadata['monte_carlo']['prediction_interval_90']['lower_percentile']
upper_90 = predicted_points + metadata['monte_carlo']['prediction_interval_90']['upper_percentile']

print(f"\nPrediction Confidence:")
print(f"  90% Interval: {lower_90:.1f} - {upper_90:.1f} points")
print(f"  Model MAE: {metadata['cv_mean_mae']:.2f} points")
print(f"  Model Stability: {metadata['cv_coefficient_of_variation']:.1f}% CV (Excellent)")

# Player consistency assessment
if pts_std_l10 < 4:
    consistency = "VERY CONSISTENT (low variance)"
    confidence = "HIGH confidence in prediction"
elif pts_std_l10 < 6:
    consistency = "CONSISTENT (moderate variance)"
    confidence = "GOOD confidence in prediction"
else:
    consistency = "VOLATILE (high variance)"
    confidence = "MODERATE confidence - player has high variance"

print(f"\n  Player consistency: {consistency}")
print(f"  Prediction confidence: {confidence}")

print("\n" + "=" * 80)
print("FEATURES USED IN PREDICTION")
print("=" * 80)
print(f"  Total features: {len(feature_cols)}")
print(f"  Player stats: {pts_l5:.1f} PPG, {min_l5:.1f} MPG, {usage_l5:.1f} usage")
print(f"  Pace features: {expected_possessions_l5:.1f} possessions")
print(f"  Positional defense: {def_pts_vs_position_l5:.1f} PPG vs {player_position}s")

print("\n" + "=" * 80 + "\n")
print("Thanks for using SharpEye.AI!")
print("\nNote: This prediction uses the locked production model with pace features.")
print(f"Model validated across {metadata['test_size']:,} games with {metadata['cv_mean_mae']:.2f} MAE.")
