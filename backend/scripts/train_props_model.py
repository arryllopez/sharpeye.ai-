"""
train_props_model.py

Goal:
- Load historical player game data
- Build features (same logic as feature_builder, but in batch)
- Train a regression model to predict stat outcome (mean)
- Compute residual std (for now, global or by bucket)
- Save model + std info to backend/models
"""

import pandas as pd
import numpy as np
# later: import xgboost as xgb

# Paths (you'll create the actual CSV later)
RAW_DATA_PATH = "data/props_history.csv"
MODEL_OUTPUT_PATH = "models/props_mean_model_placeholder.txt"
STD_OUTPUT_PATH = "models/props_residual_std_placeholder.txt"

def load_data():
    # TODO: replace with real schema
    # Example expected columns:
    #   player_name, league, stat_type, opponent, minutes, pace, actual_stat
    df = pd.read_csv(RAW_DATA_PATH)
    return df

def build_features(df: pd.DataFrame):
    # TODO: align with your PropsFeatures logic
    # For now we'll assume:
    #   recent_avg is just a rolling average or precomputed column
    #   pace_factor is a numeric column
    #   minutes_projection ~ actual minutes or projection
    feature_cols = ["recent_avg", "minutes_projection", "pace_factor"]
    X = df[feature_cols].values
    y = df["actual_stat"].values
    return X, y

def train_mean_model(X, y):
    # TODO: replace with real XGBoost
    # For now, just compute a simple global mean as a placeholder.
    mean = float(np.mean(y))
    print(f"Placeholder mean model trained, global mean: {mean:.2f}")
    # Save placeholder "model"
    with open(MODEL_OUTPUT_PATH, "w") as f:
        f.write(str(mean))
    return mean

def compute_residual_std(y, y_pred):
    residuals = y - y_pred
    std = float(residuals.std())
    print(f"Residual std: {std:.2f}")
    with open(STD_OUTPUT_PATH, "w") as f:
        f.write(str(std))
    return std

def main():
    df = load_data()
    X, y = build_features(df)

    # Placeholder: pretend model predicts global mean
    global_mean = np.mean(y)
    y_pred = np.full_like(y, global_mean, dtype=float)

    _ = train_mean_model(X, y)
    _ = compute_residual_std(y, y_pred)

    print("Training stub complete. Replace with XGBoost when ready.")

if __name__ == "__main__":
    main()
