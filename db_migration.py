import sqlite3

DB_NAME = "aquaponics.db"

REQUIRED_COLUMNS = {
    "ammonia": "REAL",
    "nitrite": "REAL",
    "nitrate": "REAL",
    "flow_rate": "REAL"
}

def migrate_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # get existing columns
    cursor.execute("PRAGMA table_info(sensor_data)")
    existing_cols = [col[1] for col in cursor.fetchall()]

    for col, col_type in REQUIRED_COLUMNS.items():
        if col not in existing_cols:
            print(f"Adding missing column: {col}")
            cursor.execute(f"ALTER TABLE sensor_data ADD COLUMN {col} {col_type}")

    conn.commit()
    conn.close()
    print("✅ Database migration completed")