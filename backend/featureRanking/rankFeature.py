import pandas as pd
import pickle
from pathlib import Path

# Absolute paths from backend root
BACKEND_ROOT = Path(__file__).parent.parent  # Goes up to backend/
MODEL_PATH = BACKEND_ROOT / "models" / "xgb_points_model_defaultParams.pkl"
FEATURES_PATH = BACKEND_ROOT / "models" / "feature_cols_default.pkl"

# Load model
with open(MODEL_PATH, 'rb') as f:
    model = pickle.load(f)

with open(FEATURES_PATH, 'rb') as f:
    feature_cols = pickle.load(f)

# Get importance
importance_df = pd.DataFrame({
    'feature': feature_cols,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print("\n" + "="*60)
print("TOP 20 FEATURES")
print("="*60)
print(importance_df.head(20).to_string(index=False))

print("\n" + "="*60)
print("NEW FEATURES ONLY")
print("="*60)
new_features = [
    'REB_L5', 'AST_L5', 'FG3M_L5', 'PTS_L3',
    'DAYS_REST', 'IS_BACK_TO_BACK',
    'USAGE_L5', 'FGA_L5', 'FG3A_L5',
    'PTS_PER_MIN_L5', 'PTS_STD_L10'
]

new_feat_df = importance_df[importance_df['feature'].isin(new_features)]
print(new_feat_df.to_string(index=False))

print("\n" + "="*60)
print("FEATURE IMPORTANCE SUMMARY")
print("="*60)
print(f"Total features: {len(feature_cols)}")
print(f"New features: {len(new_features)}")
print(f"New features in top 20: {len(new_feat_df.head(20))}")
print(f"Total importance of new features: {new_feat_df['importance'].sum():.4f}")

# Breakdown by rank
print("\n" + "="*60)
print("NEW FEATURES BY RANK")
print("="*60)
for _, row in new_feat_df.iterrows():
    rank = importance_df[importance_df['feature'] == row['feature']].index[0] + 1
    print(f"Rank {rank:3d}: {row['feature']:20s} (importance: {row['importance']:.4f})")