import sqlite3

# Create Database Connection
conn = sqlite3.connect("aquaponics.db", check_same_thread=False)

cursor = conn.cursor()

# Create Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    water_temp REAL,
    air_temp REAL,
    humidity REAL,
    ph REAL,
    oxygen REAL,
    water_level REAL
)
""")

conn.commit()


# Save Data Function
def save_data(data):

    cursor.execute("""
    INSERT INTO sensor_data (
        water_temp,
        air_temp,
        humidity,
        ph,
        oxygen,
        water_level
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["water_temp"],
        data["air_temp"],
        data["humidity"],
        data["ph"],
        data["oxygen"],
        data["water_level"]
    ))

    conn.commit()


# Read Data Function
def get_data():

    cursor.execute("SELECT * FROM sensor_data")

    return cursor.fetchall()