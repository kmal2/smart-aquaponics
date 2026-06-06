import sqlite3
import pandas as pd

conn = sqlite3.connect("aquaponics.db")

df = pd.read_sql_query(
    "SELECT * FROM sensor_data",
    conn
)

conn.close()

clean_df = df[
    (df["water_temp"] > 0) &
    (df["ph"] > 0) &
    (df["oxygen"] > 0) &
    (df["humidity"] > 0)
].copy()

def calculate_risk(row):
    risk = 0

    if row["oxygen"] < 5:
        risk += 40

    if row["water_temp"] > 30:
        risk += 25

    if row["ph"] < 6:
        risk += 20

    if row["ph"] > 8:
        risk += 20

    if row["humidity"] < 40:
        risk += 15

    return min(risk, 100)

clean_df["risk_score"] = clean_df.apply(
    calculate_risk,
    axis=1
)

print("Shape:", clean_df.shape)
print("\nDescribe:")
print(clean_df["risk_score"].describe())

print("\nDistribution:")
print(clean_df["risk_score"].value_counts().sort_index())