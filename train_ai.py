import numpy as np
import sqlite3
import pandas as pd

conn = sqlite3.connect("aquaponics.db")

df = pd.read_sql_query(
    "SELECT * FROM sensor_data",
    conn
)

conn.close()

# تنظيف البيانات
df = df[
    (df["water_temp"] > 0) &
    (df["ph"] > 0) &
    (df["oxygen"] > 0) &
    (df["humidity"] > 0)
]

# Risk Score
# Risk Score V3

df["risk_score"] = (
    abs(df["water_temp"] - 28) * 2 +
    abs(df["ph"] - 7) * 15 +
    np.maximum(0, 5 - df["oxygen"]) * 10 +
    abs(df["humidity"] - 60) * 0.3
)

# Labels
def classify(score):
    if score < 10:
        return "Healthy"
    elif score < 25:
        return "Warning"
    else:
        return "Critical"
df["status"] = df["risk_score"].apply(classify)

print(df["status"].value_counts())

df.to_csv(
    "aquaponics_training_data.csv",
    index=False
)

print("Dataset Saved")