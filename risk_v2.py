import sqlite3
import pandas as pd

conn = sqlite3.connect("aquaponics.db")
df = pd.read_sql_query("SELECT * FROM sensor_data", conn)
conn.close()

df = df[
    (df["water_temp"] > 0) &
    (df["ph"] > 0) &
    (df["oxygen"] > 0) &
    (df["humidity"] > 0)
].copy()

def risk_v2(row):

    risk = 0

    risk += abs(row["water_temp"] - 27) * 4
    risk += abs(row["ph"] - 7) * 20
    risk += abs(row["oxygen"] - 8) * 8
    risk += abs(row["humidity"] - 60) * 0.5

    return min(round(risk, 2), 100)

df["risk_score"] = df.apply(risk_v2, axis=1)

print(df["risk_score"].describe())
print()
print(df["risk_score"].head())