import sqlite3

DB_NAME = "aquaponics.db"

def insert_data(data):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("""
        INSERT INTO sensor_data (
            time, water_temp, ph, oxygen, humidity, air_temp, water_level
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, data)

        conn.commit()

    except Exception as e:
        print("DB Error:", e)

    finally:
        conn.close()