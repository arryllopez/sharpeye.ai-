"""
Analyze and visualize cross-validation results
"""

import pandas as pd
import pickle
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
MODELS_DIR = BASE_DIR / "models"

# Load CV results
cv_results = pd.read_csv(MODELS_DIR / "cv_results.csv")
metadata = pickle.load(open(MODELS_DIR / "model_metadata.pkl", "rb"))

print("=" * 80)
print("CROSS-VALIDATION RESULTS ANALYSIS")
print("=" * 80)

print("\n" + "=" * 80)
print("PERFORMANCE BY SEASON")
print("=" * 80)

for _, row in cv_results.iterrows():
    print(f"\n{row['name']}")
    print(f"  Train Size:      {row['train_size']:,} games")
    print(f"  Test Size:       {row['test_size']:,} games")
    print(f"  Train MAE:       {row['train_mae']:.3f} points")
    print(f"  Test MAE:        {row['test_mae']:.3f} points")
    print(f"  Test RMSE:       {row['test_rmse']:.3f} points")
    print(f"  Test R²:         {row['test_r2']:.3f}")
    print(f"  Within ±3 pts:   {row['within_3']:.1f}%")
    print(f"  Within ±5 pts:   {row['within_5']:.1f}%")
    print(f"  Within ±10 pts:  {row['within_10']:.1f}%")

    # Overfitting check
    overfit = row['test_mae'] - row['train_mae']
    if overfit < 0.1:
        overfit_status = "No overfitting"
    elif overfit < 0.3:
        overfit_status = "Slight overfitting (acceptable)"
    else:
        overfit_status = "Overfitting detected"

    print(f"  Overfitting:     {overfit:.3f} points ({overfit_status})")

print("\n" + "=" * 80)
print("AGGREGATED STATISTICS")
print("=" * 80)

print(f"\nTest MAE:")
print(f"  Mean:      {cv_results['test_mae'].mean():.3f} points")
print(f"  Std Dev:   {cv_results['test_mae'].std():.3f} points")
print(f"  Min:       {cv_results['test_mae'].min():.3f} points (best season)")
print(f"  Max:       {cv_results['test_mae'].max():.3f} points (worst season)")
print(f"  Range:     {cv_results['test_mae'].max() - cv_results['test_mae'].min():.3f} points")

print(f"\nTest R²:")
print(f"  Mean:      {cv_results['test_r2'].mean():.3f}")
print(f"  Std Dev:   {cv_results['test_r2'].std():.3f}")
print(f"  Min:       {cv_results['test_r2'].min():.3f}")
print(f"  Max:       {cv_results['test_r2'].max():.3f}")

print(f"\nWithin ±5 Points:")
print(f"  Mean:      {cv_results['within_5'].mean():.1f}%")
print(f"  Std Dev:   {cv_results['within_5'].std():.1f}%")
print(f"  Min:       {cv_results['within_5'].min():.1f}%")
print(f"  Max:       {cv_results['within_5'].max():.1f}%")

print("\n" + "=" * 80)
print("MODEL STABILITY METRICS")
print("=" * 80)

mae_cv = (cv_results['test_mae'].std() / cv_results['test_mae'].mean()) * 100
r2_cv = (cv_results['test_r2'].std() / cv_results['test_r2'].mean()) * 100

print(f"\nCoefficient of Variation:")
print(f"  MAE:       {mae_cv:.2f}% (lower is better)")
print(f"  R²:        {r2_cv:.2f}% (lower is better)")

if mae_cv < 5:
    stability = "EXCELLENT - Model is very stable across seasons"
elif mae_cv < 10:
    stability = "GOOD - Model shows consistent performance"
elif mae_cv < 15:
    stability = "MODERATE - Some variability across seasons"
else:
    stability = "POOR - Unstable performance, investigate feature engineering"

print(f"\nStability Rating: {stability}")

print("\n" + "=" * 80)
print("YEAR-OVER-YEAR TREND")
print("=" * 80)

print("\nTest MAE Trend:")
for i in range(len(cv_results) - 1):
    diff = cv_results.iloc[i+1]['test_mae'] - cv_results.iloc[i]['test_mae']
    direction = "UP" if diff > 0 else "DOWN"
    print(f"  Fold {i+1} -> Fold {i+2}: {direction} {abs(diff):.3f} points")

if cv_results['test_mae'].is_monotonic_increasing:
    trend = "WARNING: MAE is increasing over time (model may be degrading)"
elif cv_results['test_mae'].is_monotonic_decreasing:
    trend = "GOOD: MAE is decreasing over time (model improving)"
else:
    trend = "NORMAL: MAE fluctuates (normal variation)"

print(f"\nOverall Trend: {trend}")

print("\n" + "=" * 80)
print("COMPARISON: FINAL MODEL vs CROSS-VALIDATION")
print("=" * 80)

final_mae = metadata['final_test_mae']
cv_mean_mae = metadata['cv_mean_mae']
cv_std_mae = metadata['cv_std_mae']

print(f"\nFinal Model (80/20 split):")
print(f"  Test MAE:      {final_mae:.3f} points")
print(f"  Within ±5 pts: {metadata['final_within_5_points']:.1f}%")
print(f"  Test R²:       {metadata['final_test_r2']:.3f}")

print(f"\nCross-Validation Average:")
print(f"  Test MAE:      {cv_mean_mae:.3f} ± {cv_std_mae:.3f} points")
print(f"  Within ±5 pts: {cv_results['within_5'].mean():.1f}%")
print(f"  Test R²:       {metadata['cv_mean_r2']:.3f}")

mae_diff = final_mae - cv_mean_mae
if abs(mae_diff) < cv_std_mae:
    consistency = "GOOD: Final model performance is within CV range (consistent)"
elif mae_diff > 0:
    consistency = "WARNING: Final model slightly worse than CV average"
else:
    consistency = "GOOD: Final model better than CV average"

print(f"\nConsistency Check: {consistency}")

print("\n" + "=" * 80)
print("RECOMMENDATIONS")
print("=" * 80)

print("\n1. Model Performance:")
if cv_mean_mae < 5.0:
    print("   EXCELLENT - MAE < 5.0 points is elite for NBA prediction")
elif cv_mean_mae < 6.0:
    print("   VERY GOOD - MAE < 6.0 points is strong performance")
else:
    print("   GOOD - Consider feature engineering to improve")

print("\n2. Model Stability:")
if mae_cv < 5:
    print("   EXCELLENT - Very stable across seasons (CV < 5%)")
elif mae_cv < 10:
    print("   GOOD - Stable performance across seasons")
else:
    print("   WARNING - Consider investigating season-specific factors")

print("\n3. Overfitting Assessment:")
avg_overfit = (cv_results['test_mae'] - cv_results['train_mae']).mean()
if avg_overfit < 0.2:
    print(f"   MINIMAL - Avg overfitting: {avg_overfit:.3f} points")
elif avg_overfit < 0.5:
    print(f"   SLIGHT - Avg overfitting: {avg_overfit:.3f} points (acceptable)")
else:
    print(f"   MODERATE - Avg overfitting: {avg_overfit:.3f} points")
    print("      Consider: more regularization or more training data")

print("\n4. Deployment Readiness:")
if mae_cv < 5 and final_mae < 5.0:
    print("   READY - Model is stable and accurate enough for production")
elif mae_cv < 10 and final_mae < 6.0:
    print("   READY - Model shows good consistency and performance")
else:
    print("   REVIEW - Consider additional validation before deployment")

print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

print(f"""
Your model achieves:
  • Cross-validated MAE: {cv_mean_mae:.2f} ± {cv_std_mae:.2f} points
  • Coefficient of Variation: {mae_cv:.1f}% ({stability.split('-')[0].strip()})
  • Final Model MAE: {final_mae:.2f} points
  • Average accuracy within ±5 pts: {cv_results['within_5'].mean():.1f}%

This is {stability.lower()}.
""")

print("=" * 80 + "\n")
