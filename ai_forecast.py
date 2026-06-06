import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
import joblib

# Load data
df = pd.read_sql("SELECT * FROM sensor_data", sqlite3.connect("aquaponics.db"))

# Feature engineering (time lag)
for i in range(1, 6):
    df[f"oxygen_lag_{i}"] = df["oxygen"].shift(i)
    df[f"temp_lag_{i}"] = df["water_temp"].shift(i)
    df[f"ph_lag_{i}"] = df["ph"].shift(i)

df = df.dropna()

X = df[[col for col in df.columns if "lag" in col]]

# Predict next oxygen level
y = df["oxygen"]

model = RandomForestRegressor(n_estimators=100)
model.fit(X, y)

joblib.dump(model, "oxygen_forecast.pkl")

print("Forecast model trained")