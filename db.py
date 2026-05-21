import sqlite3

# إنشاء اتصال
conn = sqlite3.connect("aquaponics.db", check_same_thread=False)
c = conn.cursor()

# إنشاء جدول البيانات
c.execute("""
CREATE TABLE IF NOT EXISTS sensor_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT,
    water_temp REAL,
    ph REAL,
    oxygen REAL,
    humidity REAL,
    air_temp REAL,
    water_level REAL
)
""")

conn.commit()

def insert_data(data):
    c.execute("""
    INSERT INTO sensor_data (
        time, water_temp, ph, oxygen, humidity, air_temp, water_level
    ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, data)

    conn.commit()