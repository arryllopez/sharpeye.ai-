"""
Interactive NBA Player Points Predictor
Save as: backend/modeling/quick_predict.py
Run: python modeling/quick_predict.py
"""

import pandas as pd
import pickle
from pathlib import Path

# ============================================================================
# LOAD MODEL AND DATA
# ============================================================================

print("\n" + "="*70)
print("NBA PLAYER POINTS PREDICTOR")
print("="*70)
print("\nLoading model...")

# Load trained model
model_path = Path("models/xgb_points_model_defaultParams.pkl")
with open(model_path, 'rb') as f:
    model = pickle.load(f)

# Load feature columns
features_path = Path("models/feature_cols_default.pkl")
with open(features_path, 'rb') as f:
    feature_cols = pickle.load(f)

print(f"Model loaded! Uses {len(feature_cols)} features")

# Load dataset to get player stats
df = pd.read_csv("data/processed/model_dataset.csv", parse_dates=["GAME_DATE"])
df = df.sort_values("GAME_DATE")

print("Dataset loaded successfully!")

# ============================================================================
# TEAM MAPPING
# ============================================================================

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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def find_player(player_input):
    """Find player by name (case-insensitive, partial match)"""
    player_input = player_input.strip().lower()
    
    # Try exact match first
    matches = df[df['PLAYER_NAME'].str.lower() == player_input]['PLAYER_NAME'].unique()
    if len(matches) > 0:
        return matches[0]
    
    # Try partial match
    matches = df[df['PLAYER_NAME'].str.lower().str.contains(player_input)]['PLAYER_NAME'].unique()
    
    if len(matches) == 0:
        return None
    elif len(matches) == 1:
        return matches[0]
    else:
        # Multiple matches, ask user to clarify
        print(f"\nMultiple players found:")
        for i, name in enumerate(matches[:10], 1):
            print(f"  {i}. {name}")
        return None

def predict_player_points(player_name, opponent_abbr, is_home):
    """Make prediction for a player"""
    
    # Get player's recent games
    player_games = df[df['PLAYER_NAME'] == player_name].sort_values('GAME_DATE')
    
    if len(player_games) == 0:
        print(f"\n[ERROR] Player '{player_name}' not found!")
        return None
    
    # Get most recent game
    latest = player_games.iloc[-1]
    
    print(f"\n{player_name} ({latest['TEAM_ABBREVIATION']})")
    
    # Show which features are available
    available_features = latest.index.tolist()
    
    # Get opponent defense
    opponent_name = TEAM_ABBR_TO_NAME.get(opponent_abbr.upper())
    if not opponent_name:
        print(f"\n[ERROR] Invalid opponent: {opponent_abbr}")
        return None
    
    opponent_games = df[df['OPP_TEAM_NAME'] == opponent_name].sort_values('GAME_DATE')
    
    if len(opponent_games) == 0:
        print(f"\n[ERROR] No data for {opponent_name}")
        return None
    
    latest_opp = opponent_games.iloc[-1]
    
    print(f"vs {opponent_name} (allows {latest_opp['DEF_PTS_ALLOWED_L5']:.1f} PPG)")
    
    # Build features dictionary - use ALL available features from dataset
    features = {}
    
    # Add all non-team features from the player's latest game
    for col in feature_cols:
        # Skip team encoding columns (we'll add those separately)
        if col.startswith('TEAM_ABBREVIATION_') or col.startswith('OPP_TEAM_NAME_'):
            continue
        
        # Check if this feature exists in the player's data
        if col in latest.index and pd.notna(latest[col]):
            features[col] = latest[col]
        elif col in latest_opp.index and pd.notna(latest_opp[col]):
            # Try opponent data for defensive features
            features[col] = latest_opp[col]
        elif col == 'IS_HOME':
            features[col] = is_home
        else:
            # Feature not found - set to 0 (model will handle it)
            features[col] = 0
            print(f"[WARNING] Feature '{col}' not found, using 0")
    
    # Initialize all team columns as 0
    for col in feature_cols:
        if col.startswith('TEAM_ABBREVIATION_') or col.startswith('OPP_TEAM_NAME_'):
            features[col] = 0
    
    # Set player's team to 1
    player_team_col = f"TEAM_ABBREVIATION_{latest['TEAM_ABBREVIATION']}"
    if player_team_col in feature_cols:
        features[player_team_col] = 1
    
    # Set opponent team to 1
    opponent_col = f"OPP_TEAM_NAME_{opponent_name}"
    if opponent_col in feature_cols:
        features[opponent_col] = 1
    
    # Create DataFrame with features in exact order expected by model
    input_df = pd.DataFrame([features])
    
    # Ensure all required features are present
    missing_features = set(feature_cols) - set(input_df.columns)
    if missing_features:
        print(f"\n[WARNING] Missing features: {missing_features}")
        # Add missing features as 0
        for feat in missing_features:
            input_df[feat] = 0
    
    # Reorder columns to match training
    input_df = input_df[feature_cols]
    
    # Predict
    prediction = model.predict(input_df)[0]
    
    # Display result
    print("\n" + "="*70)
    print(f"PREDICTED POINTS: {prediction:.1f}")
    print("="*70)
    
    # Show recent performance if available
    if 'PTS_L5' in latest.index:
        print(f"\nRecent avg (L5): {latest['PTS_L5']:.1f} PPG")
    if 'PTS_L10' in latest.index:
        print(f"Recent avg (L10): {latest['PTS_L10']:.1f} PPG")
    
    # Show confidence range
    mae = 4.79
    print(f"\nConfidence ranges:")
    print(f"  68% likely: {prediction - mae:.1f} to {prediction + mae:.1f} points")
    print(f"  95% likely: {prediction - 2*mae:.1f} to {prediction + 2*mae:.1f} points")
    
    return prediction

# ============================================================================
# MAIN INTERACTIVE LOOP
# ============================================================================

def main():
    """Interactive prediction loop"""
    
    print("\n" + "="*70)
    print("Model features:", len(feature_cols))
    print("Sample features:", feature_cols[:10])
    print("="*70)
    
    while True:
        print("\n" + "="*70)
        
        # Get player name
        player_input = input("Enter player name (or 'quit' to exit): ").strip()
        
        if player_input.lower() in ['quit', 'exit', 'q']:
            print("\nThanks for using the predictor!")
            break
        
        if not player_input:
            print("Please enter a player name.")
            continue
        
        # Find player
        player_name = find_player(player_input)
        
        if not player_name:
            print(f"\nPlayer '{player_input}' not found. Try again with full name.")
            print("\nPopular players: LeBron James, Stephen Curry, Kevin Durant, Giannis Antetokounmpo")
            continue
        
        print(f"\nFound: {player_name}")
        
        # Get opponent
        opponent = input("Playing against (team abbreviation, e.g., LAL): ").strip().upper()
        
        if opponent not in TEAM_ABBR_TO_NAME:
            print(f"\nInvalid team abbreviation: {opponent}")
            print("Valid teams:", ", ".join(sorted(TEAM_ABBR_TO_NAME.keys())))
            continue
        
        # Get home/away
        location = input("Home or away? (h/a): ").strip().lower()
        
        if location not in ['h', 'a', 'home', 'away']:
            print("Please enter 'h' for home or 'a' for away.")
            continue
        
        is_home = 1 if location in ['h', 'home'] else 0
        
        # Make prediction
        try:
            predict_player_points(player_name, opponent, is_home)
        except Exception as e:
            print(f"\n[ERROR] Prediction failed: {e}")
            print("This might be because the model expects features not in the dataset.")
            continue
        
        # Ask to continue
        again = input("\nPredict another player? (y/n): ").strip().lower()
        if again not in ['y', 'yes']:
            print("\nThanks for using the predictor!")
            break

# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    main()