"""
Cross-validation training script for NBA player points prediction.
Tests model stability across different seasons using expanding window validation.
"""

import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score
import pickle
from pathlib import Path

# ============================
# CONFIG
# ============================
BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_PATH = BASE_DIR / "data" / "processed" / "model_dataset.csv"
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# ============================
# LOAD DATA
# ============================
print("=" * 70)
print("CROSS-VALIDATION TRAINING - NBA PLAYER POINTS")
print("=" * 70)
print("\nLoading dataset...")

df = pd.read_csv(DATASET_PATH, parse_dates=["GAME_DATE"])
df = df.sort_values(by="GAME_DATE").reset_index(drop=True)

print(f"Total rows: {len(df):,}")
print(f"Date range: {df['GAME_DATE'].min().date()} to {df['GAME_DATE'].max().date()}")

# ============================
# FEATURES
# ============================
base_features = [
    'IS_HOME',
    'PTS_L5', 'PTS_L10', 'PTS_STD_L10',
    'MIN_L5', 'PTS_PER_MIN_L5',
    'USAGE_L5', 'FGA_L5', 'FG3A_L5',
    'REB_L5', 'AST_L5', 'FG3M_L5',
    'DEF_PTS_ALLOWED_L5', 'DEF_3PT_ALLOWED_L5', 'DEF_3PT_PCT_L5',
]

# Remove missing values
df_clean = df.dropna(subset=base_features)
print(f"Rows after dropping missing: {len(df_clean):,} ({len(df_clean)/len(df)*100:.1f}%)")

# One-hot encode
df_encoded = pd.get_dummies(
    df_clean,
    columns=['TEAM_ABBREVIATION', 'OPP_TEAM_NAME'],
    drop_first=True
)

team_cols = [col for col in df_encoded.columns
             if col.startswith('TEAM_ABBREVIATION_') or col.startswith('OPP_TEAM_NAME_')]

feature_cols = base_features + team_cols

print(f"\nTotal features: {len(feature_cols)}")
print(f"  Base features: {len(base_features)}")
print(f"  Team features: {len(team_cols)}")

# ============================
# CROSS-VALIDATION SPLITS
# ============================
print("\n" + "=" * 70)
print("EXPANDING WINDOW CROSS-VALIDATION")
print("=" * 70)

# Define season boundaries (approximate)
cv_splits = [
    {
        'name': 'Train: 2021-2023 | Test: 2023-2024',
        'train_end': '2023-10-01',
        'test_start': '2023-10-01',
        'test_end': '2024-10-01',
    },
    {
        'name': 'Train: 2021-2024 | Test: 2024-2025',
        'train_end': '2024-10-01',
        'test_start': '2024-10-01',
        'test_end': '2025-10-01',
    },
    {
        'name': 'Train: 2021-2025 | Test: 2025-2026',
        'train_end': '2025-10-01',
        'test_start': '2025-10-01',
        'test_end': '2026-10-01',
    },
]

# Hyperparameters
model_params = {
    'n_estimators': 200,
    'learning_rate': 0.05,
    'max_depth': 5,
    'min_child_weight': 3,
    'subsample': 0.8,
    'colsample_bytree': 0.8,
    'random_state': 42,
    'objective': 'reg:squarederror',
    'n_jobs': -1
}

# Store results
cv_results = []

# ============================
# RUN CROSS-VALIDATION
# ============================
for i, split in enumerate(cv_splits, 1):
    print(f"\n{'=' * 70}")
    print(f"FOLD {i}: {split['name']}")
    print("=" * 70)

    # Create train/test masks
    train_mask = df_encoded['GAME_DATE'] < split['train_end']
    test_mask = (df_encoded['GAME_DATE'] >= split['test_start']) & (df_encoded['GAME_DATE'] < split['test_end'])

    x_train = df_encoded.loc[train_mask, feature_cols]
    y_train = df_encoded.loc[train_mask, 'PTS']
    x_test = df_encoded.loc[test_mask, feature_cols]
    y_test = df_encoded.loc[test_mask, 'PTS']

    print(f"\nTraining rows:  {len(x_train):,}")
    print(f"Testing rows:   {len(x_test):,}")

    if len(x_test) == 0:
        print("⚠️  No test data available for this split, skipping...")
        continue

    # Train model
    print("\nTraining XGBoost model...")
    model = xgb.XGBRegressor(**model_params)
    model.fit(x_train, y_train, verbose=False)

    # Predict
    y_train_pred = model.predict(x_train)
    y_test_pred = model.predict(x_test)

    # Evaluate
    train_mae = mean_absolute_error(y_train, y_train_pred)
    train_rmse = root_mean_squared_error(y_train, y_train_pred)
    train_r2 = r2_score(y_train, y_train_pred)

    test_mae = mean_absolute_error(y_test, y_test_pred)
    test_rmse = root_mean_squared_error(y_test, y_test_pred)
    test_r2 = r2_score(y_test, y_test_pred)

    # Accuracy breakdown
    residuals = y_test - y_test_pred
    within_3 = (abs(residuals) <= 3).mean() * 100
    within_5 = (abs(residuals) <= 5).mean() * 100
    within_10 = (abs(residuals) <= 10).mean() * 100

    # Display results
    print(f"\n{'-' * 70}")
    print("RESULTS")
    print("-" * 70)
    print(f"Train MAE:  {train_mae:.2f} points")
    print(f"Test MAE:   {test_mae:.2f} points")
    print(f"Test RMSE:  {test_rmse:.2f} points")
    print(f"Test R²:    {test_r2:.3f}")
    print(f"\nAccuracy Breakdown:")
    print(f"  Within ±3 points:  {within_3:.1f}%")
    print(f"  Within ±5 points:  {within_5:.1f}%")
    print(f"  Within ±10 points: {within_10:.1f}%")

    # Store results
    cv_results.append({
        'fold': i,
        'name': split['name'],
        'train_size': len(x_train),
        'test_size': len(x_test),
        'train_mae': train_mae,
        'test_mae': test_mae,
        'test_rmse': test_rmse,
        'test_r2': test_r2,
        'within_3': within_3,
        'within_5': within_5,
        'within_10': within_10,
    })

# ============================
# SUMMARY
# ============================
print("\n" + "=" * 70)
print("CROSS-VALIDATION SUMMARY")
print("=" * 70)

results_df = pd.DataFrame(cv_results)

print("\nTest MAE by Fold:")
for _, row in results_df.iterrows():
    print(f"  Fold {row['fold']}: {row['test_mae']:.2f} points ({row['name']})")

print(f"\nMean Test MAE:    {results_df['test_mae'].mean():.2f} ± {results_df['test_mae'].std():.2f}")
print(f"Mean Test RMSE:   {results_df['test_rmse'].mean():.2f} ± {results_df['test_rmse'].std():.2f}")
print(f"Mean Test R²:     {results_df['test_r2'].mean():.3f} ± {results_df['test_r2'].std():.3f}")
print(f"Mean Within ±5:   {results_df['within_5'].mean():.1f}% ± {results_df['within_5'].std():.1f}%")

# ============================
# MODEL STABILITY ASSESSMENT
# ============================
print("\n" + "=" * 70)
print("MODEL STABILITY ASSESSMENT")
print("=" * 70)

mae_std = results_df['test_mae'].std()
mae_mean = results_df['test_mae'].mean()
coefficient_of_variation = (mae_std / mae_mean) * 100

print(f"\nCoefficient of Variation: {coefficient_of_variation:.1f}%")

if coefficient_of_variation < 5:
    stability = "EXCELLENT - Very stable across seasons"
elif coefficient_of_variation < 10:
    stability = "GOOD - Stable performance"
elif coefficient_of_variation < 15:
    stability = "MODERATE - Some variation across seasons"
else:
    stability = "POOR - Unstable, may need feature engineering"

print(f"Stability Rating: {stability}")

# ============================
# TRAIN FINAL MODEL ON ALL DATA
# ============================
print("\n" + "=" * 70)
print("TRAINING FINAL MODEL ON ALL DATA")
print("=" * 70)

# Use 80/20 split on entire dataset
TRAIN_SPLIT = 0.8
x = df_encoded[feature_cols]
y = df_encoded['PTS']

split_idx = int(len(x) * TRAIN_SPLIT)
split_date = df_encoded.iloc[split_idx]['GAME_DATE']

x_train_final = x.iloc[:split_idx]
x_test_final = x.iloc[split_idx:]
y_train_final = y.iloc[:split_idx]
y_test_final = y.iloc[split_idx:]

print(f"\nTraining rows: {len(x_train_final):,} (up to {split_date.date()})")
print(f"Testing rows:  {len(x_test_final):,} (from {split_date.date()})")

final_model = xgb.XGBRegressor(**model_params)
final_model.fit(x_train_final, y_train_final, verbose=False)

y_test_final_pred = final_model.predict(x_test_final)
final_mae = mean_absolute_error(y_test_final, y_test_final_pred)
final_rmse = root_mean_squared_error(y_test_final, y_test_final_pred)
final_r2 = r2_score(y_test_final, y_test_final_pred)

residuals_final = y_test_final - y_test_final_pred
within_5_final = (abs(residuals_final) <= 5).mean() * 100

print(f"\nFinal Model Performance:")
print(f"  Test MAE:       {final_mae:.2f} points")
print(f"  Test RMSE:      {final_rmse:.2f} points")
print(f"  Test R²:        {final_r2:.3f}")
print(f"  Within ±5 pts:  {within_5_final:.1f}%")

# ============================
# SAVE MODEL & RESULTS
# ============================
print("\n" + "=" * 70)
print("SAVING MODEL & RESULTS")
print("=" * 70)

# Calculate residual statistics for Monte Carlo simulations
residuals_std = np.std(residuals_final)
residuals_mean = np.mean(residuals_final)

# Percentiles for prediction intervals
p5 = np.percentile(residuals_final, 5)
p95 = np.percentile(residuals_final, 95)
p10 = np.percentile(residuals_final, 10)
p90 = np.percentile(residuals_final, 90)

# Save final model (using standard naming for production)
model_path = MODELS_DIR / "xgb_points_model.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(final_model, f)
print(f"[SAVED] Model: {model_path}")

# Save features
features_path = MODELS_DIR / 'feature_cols.pkl'
with open(features_path, 'wb') as f:
    pickle.dump(feature_cols, f)
print(f"[SAVED] Features: {features_path}")

# Save metadata with CV results AND Monte Carlo parameters
metadata = {
    'version': 'cross_validated',
    'trained_date': str(pd.Timestamp.now()),

    # Final model performance
    'final_test_mae': final_mae,
    'final_test_rmse': final_rmse,
    'final_test_r2': final_r2,
    'final_within_5_points': within_5_final,
    'train_size': len(x_train_final),
    'test_size': len(x_test_final),
    'split_date': str(split_date.date()),
    'n_features': len(feature_cols),
    'hyperparameters': model_params,

    # Cross-validation results
    'cv_mean_mae': results_df['test_mae'].mean(),
    'cv_std_mae': results_df['test_mae'].std(),
    'cv_mean_r2': results_df['test_r2'].mean(),
    'cv_coefficient_of_variation': coefficient_of_variation,
    'cv_results': cv_results,

    # Monte Carlo simulation parameters
    'monte_carlo': {
        'residual_std': residuals_std,
        'residual_mean': residuals_mean,
        'prediction_interval_90': {
            'lower_percentile': p5,
            'upper_percentile': p95,
        },
        'prediction_interval_80': {
            'lower_percentile': p10,
            'upper_percentile': p90,
        },
        'recommended_std': final_rmse,  # Use RMSE as std for normal distribution
        'note': 'Use residual_std or recommended_std for Monte Carlo simulations',
    }
}

metadata_path = MODELS_DIR / 'model_metadata.pkl'
with open(metadata_path, 'wb') as f:
    pickle.dump(metadata, f)
print(f"[SAVED] Metadata: {metadata_path}")

# Save CV results as CSV for easy viewing
cv_results_path = MODELS_DIR / 'cv_results.csv'
results_df.to_csv(cv_results_path, index=False)
print(f"[SAVED] CV Results: {cv_results_path}")

print("\n" + "=" * 70)
print("MONTE CARLO SIMULATION PARAMETERS")
print("=" * 70)
print(f"\nFor Monte Carlo simulations, use:")
print(f"  Recommended Std Dev: {final_rmse:.2f} points (RMSE)")
print(f"  Residual Std Dev:    {residuals_std:.2f} points")
print(f"  Residual Mean:       {residuals_mean:.2f} points")
print(f"\n90% Prediction Interval:")
print(f"  Lower bound: {p5:.2f} points below prediction")
print(f"  Upper bound: {p95:.2f} points above prediction")
print(f"\n80% Prediction Interval:")
print(f"  Lower bound: {p10:.2f} points below prediction")
print(f"  Upper bound: {p90:.2f} points above prediction")

print("\nExample Monte Carlo usage:")
print("  prediction = model.predict(features)  # e.g., 25.3 points")
print(f"  simulations = np.random.normal(prediction, {final_rmse:.2f}, 10000)")
print("  prob_over_25_5 = (simulations > 25.5).mean()")

print("\n" + "=" * 70)
print("CROSS-VALIDATION COMPLETE")
print("=" * 70)
print(f"\nKey Takeaways:")
print(f"  • Mean CV MAE: {results_df['test_mae'].mean():.2f} ± {results_df['test_mae'].std():.2f} points")
print(f"  • Stability: {stability}")
print(f"  • Final Model MAE: {final_mae:.2f} points")
print(f"  • Monte Carlo Std: {final_rmse:.2f} points")
print("=" * 70 + "\n")
