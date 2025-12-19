# Add this to a new file: backend/diagnose_missing_defense.py
import pandas as pd

df = pd.read_csv("data/processed/model_dataset.csv", parse_dates=["GAME_DATE"])

# Check missing defense by season
df['SEASON'] = df['GAME_DATE'].apply(lambda x: f"{x.year}-{x.year+1}" if x.month >= 10 else f"{x.year-1}-{x.year}")

missing_defense = df[df['DEF_PTS_ALLOWED_L5'].isnull()]

print("Missing defensive features by season:")
print(missing_defense.groupby('SEASON').size())

print("\nMissing by opponent team:")
print(missing_defense['OPP_TEAM_NAME'].value_counts().head(10))

print(f"\nTotal games with defense data: {(~df['DEF_PTS_ALLOWED_L5'].isnull()).sum():,}")
print(f"Total games missing defense:   {df['DEF_PTS_ALLOWED_L5'].isnull().sum():,}")