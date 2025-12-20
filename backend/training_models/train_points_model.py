#imports

import pandas as pd
import numpy as np 
import xgboost as xgb
#training metrics 
from sklearn.metrics import ( 
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)

import pickle 

#handling file paths
from pathlib import Path

#define file paths
DATASET_PATH = Path("data/processed/model_dataset.csv")  
MODELS_DIR = Path("models/")        
MODELS_DIR.mkdir(exist_ok=True) 

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
    'IS_HOME',                    
    'PTS_L5',                     
    'PTS_L10',                    
    'MIN_L5',                     
    'DEF_PTS_ALLOWED_L5',        
    'DEF_3PT_ALLOWED_L5',         
    'DEF_3PT_PCT_L5',
]\

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