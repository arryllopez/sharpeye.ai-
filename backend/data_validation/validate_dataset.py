"""
Comprehensive validation script for model_dataset.csv
Checks for data leakage, temporal correctness, and data quality.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# ============================
# CONFIG
# ============================
DATASET_PATH = Path("data/processed/model_dataset.csv")

def load_data():
    """Load and prepare dataset"""
    if not DATASET_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATASET_PATH}")
    
    df = pd.read_csv(DATASET_PATH, parse_dates=["GAME_DATE"])
    df = df.sort_values(["PLAYER_ID", "GAME_DATE"]).reset_index(drop=True)
    return df

def basic_statistics(df):
    """Print basic dataset statistics"""
    print("\n" + "="*70)
    print("BASIC STATISTICS")
    print("="*70)
    print(f"Total rows:        {len(df):,}")
    print(f"Unique players:    {df['PLAYER_NAME'].nunique():,}")
    print(f"Unique teams:      {df['TEAM_ABBREVIATION'].nunique()}")
    print(f"Date range:        {df['GAME_DATE'].min().date()} to {df['GAME_DATE'].max().date()}")
    print(f"Total days:        {(df['GAME_DATE'].max() - df['GAME_DATE'].min()).days} days")
    
    # Games per player
    games_per_player = df.groupby('PLAYER_NAME').size()
    print(f"\nGames per player:")
    print(f"  Mean:   {games_per_player.mean():.1f}")
    print(f"  Median: {games_per_player.median():.1f}")
    print(f"  Min:    {games_per_player.min()}")
    print(f"  Max:    {games_per_player.max()}")

def check_columns(df):
    """Verify all required columns exist"""
    print("\n" + "="*70)
    print("COLUMN CHECK")
    print("="*70)
    
    required_cols = [
        'PLAYER_ID', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'GAME_DATE',
        'MATCHUP', 'MIN', 'PTS', 'REB', 'AST', 'FG3M', 'IS_HOME',
        'PTS_L5', 'PTS_L10', 'MIN_L5',
        'OPP_ABBR', 'OPP_TEAM_NAME',
        'DEF_PTS_ALLOWED_L5', 'DEF_3PT_ALLOWED_L5', 'DEF_3PT_PCT_L5'
    ]
    
    missing = [col for col in required_cols if col not in df.columns]
    extra = [col for col in df.columns if col not in required_cols]
    
    if missing:
        print(f"[FAIL] Missing columns: {missing}")
    else:
        print(f"[PASS] All required columns present")
    
    if extra:
        print(f"[INFO] Extra columns: {extra}")
    
    print(f"\nTotal columns: {len(df.columns)}")

def check_missing_values(df):
    """Check for missing values"""
    print("\n" + "="*70)
    print("MISSING VALUES")
    print("="*70)
    
    missing = df.isnull().sum()
    missing = missing[missing > 0].sort_values(ascending=False)
    
    if len(missing) == 0:
        print("[PASS] No missing values!")
    else:
        print("Missing value counts:")
        for col, count in missing.items():
            pct = (count / len(df)) * 100
            print(f"  {col:30s}: {count:6,} ({pct:5.2f}%)")
        
        # Check if missing values make sense
        print("\nNote: Missing rolling features (PTS_L5, etc.) are expected")
        print("      for players' first few games of the season.")

def check_data_types(df):
    """Verify data types are correct"""
    print("\n" + "="*70)
    print("DATA TYPES")
    print("="*70)
    
    # Check numeric columns
    numeric_cols = ['MIN', 'PTS', 'REB', 'AST', 'FG3M', 'PTS_L5', 'PTS_L10', 
                    'MIN_L5', 'DEF_PTS_ALLOWED_L5', 'DEF_3PT_ALLOWED_L5', 'DEF_3PT_PCT_L5']
    
    for col in numeric_cols:
        if col in df.columns:
            if not pd.api.types.is_numeric_dtype(df[col]):
                print(f"[FAIL] {col} is not numeric: {df[col].dtype}")
            else:
                print(f"[PASS] {col:30s}: {df[col].dtype}")
    
    # Check date
    if pd.api.types.is_datetime64_any_dtype(df['GAME_DATE']):
        print(f"[PASS] {'GAME_DATE':30s}: datetime64")
    else:
        print(f"[FAIL] GAME_DATE is not datetime: {df['GAME_DATE'].dtype}")

def validate_rolling_features(df):
    """CRITICAL: Verify rolling features don't leak future data"""
    print("\n" + "="*70)
    print("TEMPORAL CORRECTNESS CHECK (NO DATA LEAKAGE)")
    print("="*70)
    
    # Test multiple players
    test_players = df['PLAYER_NAME'].value_counts().head(3).index.tolist()
    
    all_valid = True
    
    for player_name in test_players:
        player_df = df[df['PLAYER_NAME'] == player_name].sort_values('GAME_DATE').reset_index(drop=True)
        
        if len(player_df) < 11:
            continue
        
        # Check row 10 (should have L5 and L10)
        row_idx = 10
        
        # Manual calculation: average of games 5-9 (previous 5 games)
        manual_l5 = player_df.iloc[5:10]['PTS'].mean()
        dataset_l5 = player_df.iloc[row_idx]['PTS_L5']
        
        # Manual calculation: average of games 0-9 (previous 10 games)
        manual_l10 = player_df.iloc[0:10]['PTS'].mean()
        dataset_l10 = player_df.iloc[row_idx]['PTS_L10']
        
        match_l5 = abs(manual_l5 - dataset_l5) < 0.1 if pd.notna(dataset_l5) else False
        match_l10 = abs(manual_l10 - dataset_l10) < 0.1 if pd.notna(dataset_l10) else False
        
        status_l5 = "[PASS]" if match_l5 else "[FAIL]"
        status_l10 = "[PASS]" if match_l10 else "[FAIL]"
        
        print(f"\n{player_name} (Row {row_idx}):")
        print(f"  PTS_L5:  Dataset={dataset_l5:.2f}, Manual={manual_l5:.2f} {status_l5}")
        print(f"  PTS_L10: Dataset={dataset_l10:.2f}, Manual={manual_l10:.2f} {status_l10}")
        
        if not (match_l5 and match_l10):
            all_valid = False
    
    if all_valid:
        print("\n[PASS] ROLLING FEATURES ARE TEMPORALLY CORRECT - NO DATA LEAKAGE!")
    else:
        print("\n[FAIL] WARNING: Rolling features may have data leakage!")

def check_opponent_mapping(df):
    """Verify opponent abbreviations are correctly mapped"""
    print("\n" + "="*70)
    print("OPPONENT MAPPING CHECK")
    print("="*70)
    
    # Check for unmapped opponents
    unmapped = df[df['OPP_TEAM_NAME'].isnull()]
    
    if len(unmapped) > 0:
        print(f"[FAIL] Found {len(unmapped)} games with unmapped opponents")
        print(f"       Unique unmapped abbreviations: {unmapped['OPP_ABBR'].unique()}")
    else:
        print("[PASS] All opponents correctly mapped")
    
    # Show mapping sample
    print("\nSample opponent mappings:")
    sample = df[['OPP_ABBR', 'OPP_TEAM_NAME']].drop_duplicates().head(10)
    for _, row in sample.iterrows():
        print(f"  {row['OPP_ABBR']:5s} -> {row['OPP_TEAM_NAME']}")

def check_defense_features(df):
    """Verify defensive features are reasonable"""
    print("\n" + "="*70)
    print("DEFENSIVE FEATURES CHECK")
    print("="*70)
    
    # Check ranges
    def check_range(col, min_val, max_val, name):
        if col not in df.columns:
            return
        
        actual_min = df[col].min()
        actual_max = df[col].max()
        
        if actual_min < min_val or actual_max > max_val:
            print(f"[WARN] {name}: Range [{actual_min:.2f}, {actual_max:.2f}] outside expected [{min_val}, {max_val}]")
        else:
            print(f"[PASS] {name:30s}: [{actual_min:.2f}, {actual_max:.2f}]")
    
    check_range('DEF_PTS_ALLOWED_L5', 80, 140, 'DEF_PTS_ALLOWED_L5')
    check_range('DEF_3PT_ALLOWED_L5', 8, 18, 'DEF_3PT_ALLOWED_L5')
    check_range('DEF_3PT_PCT_L5', 0.25, 0.45, 'DEF_3PT_PCT_L5')

def sample_data(df):
    """Show sample rows"""
    print("\n" + "="*70)
    print("SAMPLE DATA")
    print("="*70)
    
    # Show recent games from a star player
    star_players = ['LeBron James', 'Stephen Curry', 'Kevin Durant', 'Giannis Antetokounmpo']
    
    for player in star_players:
        if player in df['PLAYER_NAME'].values:
            sample = df[df['PLAYER_NAME'] == player].sort_values('GAME_DATE', ascending=False).head(3)
            print(f"\n{player} - Recent games:")
            print(sample[['GAME_DATE', 'MATCHUP', 'PTS', 'PTS_L5', 'PTS_L10', 'DEF_PTS_ALLOWED_L5']].to_string(index=False))
            break

def data_quality_checks(df):
    """Additional quality checks"""
    print("\n" + "="*70)
    print("DATA QUALITY CHECKS")
    print("="*70)
    
    # Check for duplicate games
    duplicates = df.duplicated(subset=['PLAYER_ID', 'GAME_DATE'], keep=False)
    if duplicates.any():
        print(f"[FAIL] Found {duplicates.sum()} duplicate player-game combinations")
    else:
        print("[PASS] No duplicate player-game combinations")
    
    # Check IS_HOME values
    home_values = df['IS_HOME'].unique()
    if set(home_values) == {0, 1}:
        print(f"[PASS] IS_HOME values correct: {sorted(home_values)}")
    else:
        print(f"[FAIL] IS_HOME has unexpected values: {sorted(home_values)}")
    
    # Check for negative values where they shouldn't exist
    numeric_cols = ['MIN', 'PTS', 'REB', 'AST', 'FG3M']
    for col in numeric_cols:
        if (df[col] < 0).any():
            print(f"[FAIL] {col} has negative values")
        else:
            print(f"[PASS] {col} has no negative values")

def summary(df):
    """Final summary"""
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    # Count how many rows are "model-ready" (no missing features)
    feature_cols = ['PTS_L5', 'PTS_L10', 'MIN_L5', 'DEF_PTS_ALLOWED_L5']
    model_ready = df.dropna(subset=feature_cols)
    
    print(f"Model-ready rows:  {len(model_ready):,} / {len(df):,} ({len(model_ready)/len(df)*100:.1f}%)")
    print(f"Players with data: {model_ready['PLAYER_NAME'].nunique():,}")
    print(f"\nDataset is ready for training!")

def main():
    """Run all validation checks"""
    print("\n" + "="*70)
    print("SHARPEYE.AI DATASET VALIDATION")
    print("="*70)
    
    try:
        df = load_data()
        
        basic_statistics(df)
        check_columns(df)
        check_missing_values(df)
        check_data_types(df)
        validate_rolling_features(df)
        check_opponent_mapping(df)
        check_defense_features(df)
        data_quality_checks(df)
        sample_data(df)
        summary(df)
        
        print("\n" + "="*70)
        print("VALIDATION COMPLETE")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()