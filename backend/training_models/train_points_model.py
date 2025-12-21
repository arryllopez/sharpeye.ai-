#imports

import pandas as pd
import numpy as np 
import xgboost as xgb
#training metrics 
from sklearn.metrics import ( 
    mean_absolute_error,
    #need to use root mean squared error
    root_mean_squared_error, 
    mean_squared_error,
    r2_score,
)

import pickle 

#handling file paths
from pathlib import Path

#define file paths
BASE_DIR = Path(__file__).resolve().parents[1]  # backend/
DATASET_PATH = BASE_DIR / "data" / "processed" / "model_dataset.csv"
#output model path
MODELS_DIR = BASE_DIR / "models"       
MODELS_DIR.mkdir(parents = True, exist_ok=True) 

#using 80% of the dataset for training and 20% for testing
TRAIN_SPLIT = 0.8

print ("--------")
print ("Loading Dataset...") 
print ("--------") 

#load dataset into a pandas dataframe
#parse_dates will convert game date column into datetime objects
df = pd.read_csv(DATASET_PATH, parse_dates=["GAME_DATE"])

#sorting by date oldest-latest 
df = df.sort_values(by="GAME_DATE").reset_index(drop=True)

# Display basic info about the dataset
print(f"Total rows: {len(df):,}")  # :, adds comma separators (103,836)
print(f"Date range: {df['GAME_DATE'].min().date()} to {df['GAME_DATE'].max().date()}")

#include the features for training
base_features = [  
    #adding the new features
    # context
    'IS_HOME',

    # scoring trends
    'PTS_L5',
    'PTS_L10',
    'PTS_STD_L10',

    # minutes / role
    'MIN_L5',
    'PTS_PER_MIN_L5',

    # usage & volume
    'USAGE_L5',
    'FGA_L5',
    'FG3A_L5',

    # peripherals (stability indicators)
    'REB_L5',
    'AST_L5',
    'FG3M_L5',

    # defense
    'DEF_PTS_ALLOWED_L5',
    'DEF_3PT_ALLOWED_L5',
    'DEF_3PT_PCT_L5',
]

#removing rows with no features (early season games) 
df_clean = df.dropna(subset=base_features)
print(f"Rows after dropping missing: {len(df_clean):,} ({len(df_clean)/len(df)*100:.1f}%)")

#one-hot encoding categorical variables
df_encoded = pd.get_dummies(
    df_clean,                                         # Input dataframe
    columns=['TEAM_ABBREVIATION', 'OPP_TEAM_NAME'],  # Columns to encode
    drop_first=True                                   # Drop first category to avoid redundancy
    # drop_first=True prevents "dummy variable trap" where columns are perfectly correlated
)

team_cols = [col for col in df_encoded.columns 
             if col.startswith('TEAM_ABBREVIATION_') or col.startswith('OPP_TEAM_NAME_')]


feature_cols = base_features + team_cols

print(f"Total features: {len(feature_cols)}")
print(f"  Base features: {len(base_features)}")
print(f"  Team features: {len(team_cols)}")

x = df_encoded[feature_cols]
y = df_encoded['PTS']

#displaying dataset statistics
print(f"\nTarget (PTS) statistics:")
print(f"  Mean:   {y.mean():.2f}")       # Average points scored
print(f"  Median: {y.median():.2f}")     # Middle value
print(f"  Std:    {y.std():.2f}")        # Standard deviation (spread)
print(f"  Min:    {y.min()}")            # Lowest points in dataset
print(f"  Max:    {y.max()}")            # Highest points in dataset

#splitting dataset into training and testing sets

split_idx = int(len(x) * TRAIN_SPLIT ) #calcuialting splitn at 80%  mark of dataset
split_date = df_encoded.iloc[split_idx]['GAME_DATE'] #what date does the split occur

x_train = x.iloc[:split_idx] 
x_test = x.iloc[split_idx:]
y_train = y.iloc[:split_idx]
y_test = y.iloc[split_idx:]

print("\nDataset split:")
print(f"  Training rows: {len(x_train):,} (up to {split_date.date()})")
print(f"  Testing rows:  {len(x_test):,} (from {split_date.date()})")
print("--------")

#training the XGBoost model
print("Training XGBoost model...")
#initialize the modela nd specify hyperparameters, standard version
model = xgb.XGBRegressor(
    n_estimators=200,          # Build 200 trees
    learning_rate=0.05,        # Each tree contributes 5%
    max_depth=5,               # Trees can split 5 levels deep
    min_child_weight=3,        # Min 3 samples per leaf
    subsample=0.8,             # Use 80% of data per tree
    colsample_bytree=0.8,      # Use 80% of features per tree
    random_state=42,
    objective='reg:squarederror',
    n_jobs=-1
)

print("\nHyperparameters:")
print(f"  n_estimators:     {model.n_estimators}")
print(f"  learning_rate:    {model.learning_rate}")
print(f"  max_depth:        {model.max_depth}")
print(f"  min_child_weight: {model.min_child_weight}")
print(f"  subsample:        {model.subsample}")
print(f"  colsample_bytree: {model.colsample_bytree}")

#commence training
print("\nTraining...")
model.fit(x_train, y_train, verbose=False)
print("Training complete!")

#make predicitons on training and testing sets
y_train_pred = model.predict(x_train)
y_test_pred = model.predict(x_test)

#model evaluation metrics
train_mae = mean_absolute_error(y_train, y_train_pred)
train_rmse = root_mean_squared_error(y_train, y_train_pred)
train_r2 = r2_score(y_train, y_train_pred)

test_mae = mean_absolute_error(y_test, y_test_pred)
test_rmse = root_mean_squared_error(y_test, y_test_pred)
test_r2 = r2_score(y_test, y_test_pred)

#display training and testing metrics adn i used claudeAI to translat eand format what each metric means
print("\n" + "=" * 70)
print("MODEL ACCURACY RESULTS")
print("=" * 70)

# --------------------------------------------------
# [1] MAE
# --------------------------------------------------
print("\n[1] MAE (Mean Absolute Error) — MOST IMPORTANT")
print("-" * 70)
print(f"Test MAE: {test_mae:.2f} points")

print("\nWhat this means:")
print(f"  - On average, predictions are off by {test_mae:.2f} points")
print(f"  - Example: Predict 25 pts, actual could be {25-test_mae:.1f} to {25+test_mae:.1f}")

if test_mae < 4.5:
    accuracy_rating = "EXCELLENT"
    accuracy_percent = "~92–95%"
    verdict = "Elite model! Predictions are highly reliable."
elif test_mae < 5.5:
    accuracy_rating = "VERY GOOD"
    accuracy_percent = "~88–92%"
    verdict = "Strong model! Great for sports betting."
elif test_mae < 6.5:
    accuracy_rating = "GOOD"
    accuracy_percent = "~85–88%"
    verdict = "Solid model! Usable for betting."
elif test_mae < 8.0:
    accuracy_rating = "OKAY"
    accuracy_percent = "~80–85%"
    verdict = "Decent but needs improvement."
else:
    accuracy_rating = "NEEDS WORK"
    accuracy_percent = "~75–80%"
    verdict = "Add more features or tune parameters."

print(f"\nRating: {accuracy_rating}")
print(f"Effective Accuracy: {accuracy_percent} accurate")
print(f"Verdict: {verdict}")

# --------------------------------------------------
# [2] RMSE
# --------------------------------------------------
print("\n[2] RMSE (Root Mean Squared Error)")
print("-" * 70)
print(f"Test RMSE: {test_rmse:.2f} points")

print("\nWhat this means:")
print("  - Average prediction error, but large mistakes are penalized more heavily")
print("  - Measured in the same units as the target variable (points)")
print("  - Sensitive to outliers (big misses hurt the score more)")

rmse_mae_ratio = test_rmse / test_mae
print(f"  - RMSE / MAE ratio: {rmse_mae_ratio:.2f}")

if rmse_mae_ratio < 1.3:
    print("  - Good! Errors are consistent (no wild predictions)")
else:
    print("  - Warning: Some predictions are significantly off")

# --------------------------------------------------
# [3] R²
# --------------------------------------------------
print("\n[3] R² Score (How Much Variance Is Explained)")
print("-" * 70)
print(f"Test R²: {test_r2:.3f}")

print("\nWhat this means:")
r2_percent = test_r2 * 100
print(f"  - Model explains {r2_percent:.1f}% of why points vary")
print(f"  - Remaining {100 - r2_percent:.1f}% is due to unpredictable factors")
print("    (injuries, hot/cold streaks, coaching decisions, etc.)")

if test_r2 > 0.75:
    print("  - Excellent! Very predictive model")
elif test_r2 > 0.65:
    print("  - Good! Strong predictive power")
elif test_r2 > 0.50:
    print("  - Okay! Moderate predictive power")
else:
    print("  - Weak! Model struggles to predict accurately")

# --------------------------------------------------
# [4] Prediction Accuracy Breakdown
# --------------------------------------------------
print("\n[4] Prediction Accuracy Breakdown")
print("-" * 70)

residuals = y_test - y_test_pred
within_3 = (abs(residuals) <= 3).mean() * 100
within_5 = (abs(residuals) <= 5).mean() * 100
within_10 = (abs(residuals) <= 10).mean() * 100

print(f"Predictions within ±3 points:  {within_3:.1f}%")
print(f"Predictions within ±5 points:  {within_5:.1f}%")
print(f"Predictions within ±10 points: {within_10:.1f}%")

print("\nWhat this means for betting:")
if within_5 > 60:
    print("  - EXCELLENT: Most predictions are very close to actual outcomes")
elif within_5 > 50:
    print("  - GOOD: Predictions are generally reliable for betting")
else:
    print("  - FAIR: Use with caution for betting")


#save the trained model
print ("\nSaving model...")

model_path = MODELS_DIR / "xgb_points_model_defaultParams.pkl"
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
print(f"[SAVED] Model: {model_path}")

features_path = MODELS_DIR / 'feature_cols_default.pkl'
with open(features_path, 'wb') as f:
    pickle.dump(feature_cols, f)
print(f"[SAVED] Features: {features_path}")

metadata = {
    'version': 'default',
    'test_mae': test_mae,
    'test_rmse': test_rmse,
    'test_r2': test_r2,
    'within_5_points': within_5,
    'train_size': len(x_train),
    'test_size': len(x_test),
    'split_date': str(split_date.date()),
    'n_features': len(feature_cols),
    'hyperparameters': {
        'n_estimators': 200,
        'learning_rate': 0.05,
        'max_depth': 5,
        'min_child_weight': 3,
        'subsample': 0.8,
        'colsample_bytree': 0.8
    }
}

metadata_path = MODELS_DIR / 'model_metadata_default.pkl'
with open(metadata_path, 'wb') as f:
    pickle.dump(metadata, f)
print(f"[SAVED] Metadata: {metadata_path}")

# ============================
# SUMMARY
# ============================
print("\n" + "="*70)
print("FINAL SUMMARY - DEFAULT PARAMETERS")
print("="*70)
print(f"\nTest MAE:        {test_mae:.2f} points")
print(f"Accuracy Rating: {accuracy_rating}")
print(f"Within ±5 pts:   {within_5:.1f}%")
print(f"R² Score:        {test_r2:.3f}")
print(f"\nVerdict: {verdict}")
print("="*70 + "\n")

#using plots to display how well regression fitted
import matplotlib.pyplot as plt
# Use row index for x-axis
row_idx = y_test.index  # original CSV row indices

plt.figure(figsize=(12, 6))

# Plot actual points as integers
plt.scatter(row_idx, y_test.astype(int), color='green', alpha=0.6, label='Actual Points')

# Plot predicted points as floats
plt.scatter(row_idx, y_test_pred, color='blue', alpha=0.6, label='Predicted Points')

plt.xlabel("Row Index in CSV / Game Order")
plt.ylabel("Points")
plt.title("Actual vs Predicted Points per Game (Row-level)")
plt.legend()
plt.grid(True)

plt.show()