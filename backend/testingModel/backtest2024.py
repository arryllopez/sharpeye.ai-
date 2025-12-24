#backtesting the model on betting lines from the 2024-2025 NBA season

import pandas as pd
import numpy as np
import pickle
from pathlib import Path
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

#file output paths and input paths
OUTPUT_DIR = Path("testingModel/backtest2024Results")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_PATH = Path("models/xgb_points_model_defaultParams.pkl")
FEATURES_PATH = Path("models/feature_cols_default.pkl")
DATASET_PATH = Path("data/processed/model_dataset.csv")

# altered the backtesting script to test on 2024-2025 season (regular season only) 
SEASON_START = "2024-10-22"
SEASON_END = "2025-04-13"

print("----------")
print("SHARPEYE.AI - 2024-25 SEASON BACKTESTING")
print("----------")

#loading the model and datasets

print("\nLoading model and data...")

with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)
print(f"[LOADED] Model: {MODEL_PATH}")

with open(FEATURES_PATH, 'rb') as f:
    feature_cols = pickle.load(f)
print(f"[LOADED] Features: {len(feature_cols)}")

df = pd.read_csv(DATASET_PATH, parse_dates=["GAME_DATE"])
df = df.sort_values("GAME_DATE")
print(f"[LOADED] Dataset: {len(df):,} games")

# ============================================================================
# FILTER TO 2024-25 SEASON
# ============================================================================

print("\n" + "="*70)
print("FILTERING TO 2024-25 SEASON")
print("="*70)

season_df = df[
    (df['GAME_DATE'] >= SEASON_START) & 
    (df['GAME_DATE'] <= SEASON_END)
].copy()

# Remove games without features (early season games)
season_df = season_df.dropna(subset=['PTS_L5', 'PTS_L10', 'MIN_L5', 
                                      'DEF_PTS_ALLOWED_L5', 'DEF_3PT_ALLOWED_L5'])

print(f"\nSeason date range: {season_df['GAME_DATE'].min().date()} to {season_df['GAME_DATE'].max().date()}")
print(f"Total games: {len(season_df):,}")
print(f"Unique players: {season_df['PLAYER_NAME'].nunique():,}")
print(f"Total teams: {season_df['TEAM_ABBREVIATION'].nunique()}")

# ============================================================================
# PREPARE DATA FOR PREDICTION
# ============================================================================

print("\nPreparing features...")

# One-hot encode teams
df_encoded = pd.get_dummies(
    season_df,
    columns=['TEAM_ABBREVIATION', 'OPP_TEAM_NAME'],
    drop_first=True
)

# Ensure all feature columns exist
for col in feature_cols:
    if col not in df_encoded.columns:
        df_encoded[col] = 0

X = df_encoded[feature_cols]
y_actual = df_encoded['PTS'].values

# ============================================================================
# MAKE PREDICTIONS
# ============================================================================

print("\nGenerating predictions for entire season...")

y_pred = model.predict(X)

season_df['prediction'] = y_pred # this stores the absolute prediction the model makes from the game
season_df['error'] = np.abs(y_actual - y_pred) #absolute error (how far off the model was)
season_df['error_signed'] = y_actual - y_pred #signed error (to check for bias)
# if the model is under predicting more often than over predicting then y_actual - y_pred will be positive on average
# if the model is over predicting more often than under predicting then y_actual - y_pred will be negative on average
# an average of this column will show if the model is biased in either direction
# ≈ 0 → no systematic bias, 0 → model tends to predict too low, 0 → model tends to predict too high

# ============================================================================
# CALCULATE OVERALL METRICS
# ============================================================================

print("\n" + "="*70)
print("OVERALL SEASON PERFORMANCE")
print("="*70)

mae = mean_absolute_error(y_actual, y_pred)
rmse = root_mean_squared_error(y_actual, y_pred)
r2 = r2_score(y_actual, y_pred)

#measuring relevant accuracy

within_3 = (season_df['error'] <= 3).mean() * 100
within_5 = (season_df['error'] <= 5).mean() * 100
within_7 = (season_df['error'] <= 7).mean() * 100
within_10 = (season_df['error'] <= 10).mean() * 100

print(f"\nPrediction Accuracy:")
print(f"  MAE:  {mae:.2f} points")
print(f"  RMSE: {rmse:.2f} points")
print(f"  R²:   {r2:.3f}")

print(f"\nAccuracy Distribution:")
print(f"  Within ±3 points:  {within_3:.1f}%")
print(f"  Within ±5 points:  {within_5:.1f}%")
print(f"  Within ±7 points:  {within_7:.1f}%")
print(f"  Within ±10 points: {within_10:.1f}%")

# detecting systematic bias 
mean_error = season_df['error_signed'].mean()
print(f"\nModel Bias:")
print(f"  Mean signed error: {mean_error:+.2f} points")
if abs(mean_error) < 0.5: # unbiased , closer to zero the better
    print(f"  Status: Unbiased (well-calibrated)")
elif mean_error > 0: #positive value
    print(f"  Status: Slight over-prediction bias")
else: #negatiove vlaue
    print(f"  Status: Slight under-prediction bias")

# ============================================================================
# PERFORMANCE BY PLAYER TYPE
# ============================================================================

print("\n" + "="*70)
print("PERFORMANCE BY PLAYER SCORING LEVEL")
print("="*70)

# Categorize players by scoring average
season_df['scoring_category'] = pd.cut(
    season_df['PTS'],
    bins=[0, 10, 20, 30, 100],
    labels=['Low (0-10)', 'Medium (10-20)', 'High (20-30)', 'Elite (30+)']
)

by_scoring = season_df.groupby('scoring_category').agg({
    'error': ['count', 'mean'],
    'PTS': 'mean'
}).round(2)

by_scoring.columns = ['games', 'avg_error', 'avg_points']

print("\nAccuracy by Scoring Level:")
print(by_scoring.to_string())

# ============================================================================
# TOP 10 BEST PREDICTED PLAYERS
# ============================================================================

print("----------------------------------------------")
print("TOP 10 MOST ACCURATELY PREDICTED PLAYERS (min 20 games)")
print("----------------------------------------------")

player_stats = season_df.groupby('PLAYER_NAME').agg({
    'PTS': ['count', 'mean'],
    'error': 'mean'
}).round(2)

player_stats.columns = ['games', 'avg_points', 'avg_error']
player_stats = player_stats[player_stats['games'] >= 20]
player_stats = player_stats.sort_values('avg_error')

print("\nBest Predicted Players:")
for i, (player, stats) in enumerate(player_stats.head(10).iterrows(), 1):
    print(f"{i:2d}. {player:30s} | {stats['games']:3.0f} games | {stats['avg_points']:4.1f} PPG | ±{stats['avg_error']:.2f} error")

# ============================================================================
# TOP 10 WORST PREDICTED PLAYERS
# ============================================================================

print("----------------------------------------------")
print("TOP 10 HARDEST TO PREDICT PLAYERS (min 20 games)")
print("----------------------------------------------")

print("\nHardest to Predict:")
for i, (player, stats) in enumerate(player_stats.tail(10).iloc[::-1].iterrows(), 1):
    print(f"{i:2d}. {player:30s} | {stats['games']:3.0f} games | {stats['avg_points']:4.1f} PPG | ±{stats['avg_error']:.2f} error")

# ============================================================================
# PERFORMANCE BY HOME/AWAY
# ============================================================================

print("----------------------------------------------")
print("HOME vs AWAY PERFORMANCE")
print("----------------------------------------------")

by_location = season_df.groupby('IS_HOME').agg({
    'error': ['count', 'mean'],
    'PTS': 'mean'
}).round(2)

by_location.columns = ['games', 'avg_error', 'avg_points']
by_location.index = ['Away', 'Home']

print(by_location.to_string())

# ============================================================================
# PERFORMANCE BY MONTH
# ============================================================================

print("\n" + "="*70)
print("PERFORMANCE BY MONTH")
print("="*70)

season_df['month_period'] = season_df['GAME_DATE'].dt.to_period('M')

by_month = (
    season_df
    .groupby('month_period')
    .agg(
        games=('error', 'count'),
        avg_error=('error', 'mean'),
        avg_points=('PTS', 'mean')
    )
    .round(2)
    .sort_index()
)

print(by_month.to_string())



# ============================================================================
# SAMPLE PREDICTIONS
# ============================================================================

print("\n" + "="*70)
print("SAMPLE PREDICTIONS - MOST ACCURATE")
print("="*70)

best_predictions = season_df.nsmallest(5, 'error')

for _, game in best_predictions.iterrows():
    print(f"\n{game['PLAYER_NAME']} ({game['GAME_DATE'].date()})")
    print(f"  Predicted: {game['prediction']:.1f} points")
    print(f"  Actual:    {game['PTS']:.0f} points")
    print(f"  Error:     ±{game['error']:.1f} points")

print("\n" + "="*70)
print("SAMPLE PREDICTIONS - BIGGEST MISSES")
print("="*70)

worst_predictions = season_df.nlargest(5, 'error')

for _, game in worst_predictions.iterrows():
    print(f"\n{game['PLAYER_NAME']} ({game['GAME_DATE'].date()})")
    print(f"  Predicted: {game['prediction']:.1f} points")
    print(f"  Actual:    {game['PTS']:.0f} points")
    print(f"  Error:     ±{game['error']:.1f} points")
    print(f"  Context:   {game['MATCHUP']}")

# ============================================================================
# VISUALIZATIONS USING MATPLOTLIB
# ============================================================================

print("\n" + "="*70)
print("GENERATING VISUALIZATIONS")
print("="*70)

fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Plot 1: Prediction vs Actual (scatter)
axes[0, 0].scatter(y_actual, y_pred, alpha=0.3, s=10)
axes[0, 0].plot([0, 80], [0, 80], 'r--', linewidth=2, label='Perfect Prediction')
axes[0, 0].set_xlabel('Actual Points')
axes[0, 0].set_ylabel('Predicted Points')
axes[0, 0].set_title('Predicted vs Actual Points (2024-25 Season)', fontweight='bold')
axes[0, 0].legend()
axes[0, 0].grid(alpha=0.3)

# Plot 2: Error distribution
axes[0, 1].hist(season_df['error'], bins=50, edgecolor='black', alpha=0.7)
axes[0, 1].axvline(x=mae, color='r', linestyle='--', linewidth=2, label=f'MAE = {mae:.2f}')
axes[0, 1].set_xlabel('Absolute Error (points)')
axes[0, 1].set_ylabel('Frequency')
axes[0, 1].set_title('Prediction Error Distribution', fontweight='bold')
axes[0, 1].legend()
axes[0, 1].grid(alpha=0.3)

# Plot 3: MAE over time (rolling 100-game window)
rolling_mae = season_df['error'].rolling(window=100, min_periods=1).mean()
axes[1, 0].plot(range(len(rolling_mae)), rolling_mae, linewidth=2)
axes[1, 0].axhline(y=mae, color='r', linestyle='--', alpha=0.5, label=f'Overall MAE = {mae:.2f}')
axes[1, 0].set_xlabel('Game Number')
axes[1, 0].set_ylabel('MAE (points)')
axes[1, 0].set_title('Rolling MAE Over Season (100-game window)', fontweight='bold')
axes[1, 0].legend()
axes[1, 0].grid(alpha=0.3)

# Plot 4: Accuracy by scoring level
scoring_accuracy = season_df.groupby('scoring_category')['error'].mean()
axes[1, 1].bar(range(len(scoring_accuracy)), scoring_accuracy.values, 
               tick_label=scoring_accuracy.index, alpha=0.7, edgecolor='black')
axes[1, 1].axhline(y=mae, color='r', linestyle='--', alpha=0.5, label='Overall MAE')
axes[1, 1].set_xlabel('Player Scoring Level')
axes[1, 1].set_ylabel('Average Error (points)')
axes[1, 1].set_title('Prediction Accuracy by Scoring Level', fontweight='bold')
axes[1, 1].legend()
axes[1, 1].grid(alpha=0.3, axis='y')
plt.xticks(rotation=45, ha='right')

plt.tight_layout()
plot_path = OUTPUT_DIR / "backtest_2024_season_results.png"

plt.tight_layout()
plt.savefig(plot_path, dpi=300, bbox_inches="tight")

print(f"\n[SAVED] Visualization saved as: {plot_path}")

# ============================================================================
# SAVE DETAILED RESULTS
# ============================================================================

print("\n" + "="*70)
print("SAVING RESULTS")
print("="*70)

# Save predictions to CSV
output_df = season_df[[
    'GAME_DATE', 'PLAYER_NAME', 'TEAM_ABBREVIATION', 'MATCHUP',
    'PTS', 'prediction', 'error', 'IS_HOME'
]].copy()

output_df.columns = [
    'Date', 'Player', 'Team', 'Matchup', 
    'Actual_Points', 'Predicted_Points', 'Error', 'Home_Game'
]

output_path = OUTPUT_DIR / "backtest_2024_season_predictions.csv"
output_df.to_csv(output_path, index=False)
print(f"[SAVED] Detailed predictions: {output_path}")

# Save summary statistics
summary = {
    'season': '2024-25',
    'total_games': len(season_df),
    'mae': mae,
    'rmse': rmse,
    'r2': r2,
    'within_5_pct': within_5,
    'within_10_pct': within_10,
    'unique_players': season_df['PLAYER_NAME'].nunique()
}

summary_df = pd.DataFrame([summary])
summary_path = OUTPUT_DIR / "backtest_2024_season_summary.csv"
summary_df.to_csv(summary_path, index=False)

print(f"[SAVED] Summary statistics: {summary_path}")


# ============================================================================
# FINAL SUMMARY
# ============================================================================

print("\n" + "="*70)
print("BACKTESTING COMPLETE - 2024-25 SEASON")
print("="*70)

print(f"\nKey Findings:")
print(f"  ✓ Backtested on {len(season_df):,} player performances from {season_df['GAME_DATE'].min().date()} to {season_df['GAME_DATE'].max().date()}")
print(f"  ✓ Achieved {mae:.2f} MAE across full season")
print(f"  ✓ {within_5:.1f}% of predictions within ±5 points")
print(f"  ✓ {within_10:.1f}% of predictions within ±10 points")
print (f"  ✓ Model bias: Mean signed error of {mean_error:+.2f} points")

