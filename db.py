import sqlite3

DB_NAME = "aquaponics.db"

def insert_data(data):
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()

        c.execute("""
        INSERT INTO sensor_data (
            time,
            water_temp,
            ph,
            oxygen,
            humidity,
            air_temp,
            water_level,
            ammonia,
            nitrite,
            nitrate,
            flow_rate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)

        conn.commit()

    except Exception as e:
        print("DB Error:", e)

    finally:
        conn.close()
# --- أضف هذا الكود في نهاية ملف db.py الخاص بك ---

def init_fish_table():
    """إنشاء جدول لحفظ وإدارة بيانات الأسماك إذا لم يكن موجوداً"""
    conn = sqlite3.connect("aquaponics.db")
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS fish_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        fish_count INTEGER,
        avg_weight REAL,
        feeding_rate REAL
    )
    """)
    # إذا كان الجدول فارغاً تماماً، نضع قراءة أولية افتراضية
    c.execute("SELECT COUNT(*) FROM fish_stock")
    if c.fetchone()[0] == 0:
        import datetime
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO fish_stock (timestamp, fish_count, avg_weight, feeding_rate) VALUES (?, ?, ?, ?)",
                  (now, 100, 200.0, 2.0))
    conn.commit()
    conn.close()

def save_fish_settings(fish_count, avg_weight, feeding_rate):
    """حفظ التحديثات الجديدة للأسماك في قاعدة البيانات"""
    import datetime
    conn = sqlite3.connect("aquaponics.db")
    c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""
    INSERT INTO fish_stock (timestamp, fish_count, avg_weight, feeding_rate)
    VALUES (?, ?, ?, ?)
    """, (now, fish_count, avg_weight, feeding_rate))
    conn.commit()
    conn.close()

def load_latest_fish_settings():
    """جلب آخر تحديث لبيانات الأسماك من قاعدة البيانات"""
    init_fish_table() # التأكد من وجود الجدول أولاً
    conn = sqlite3.connect("aquaponics.db")
    c = conn.cursor()
    c.execute("SELECT fish_count, avg_weight, feeding_rate FROM fish_stock ORDER BY id DESC LIMIT 1")
    row = c.fetchone()
    conn.close()
    if row:
        return {"fish_count": row[0], "avg_weight": row[1], "feeding_rate": row[2]}
    return {"fish_count": 100, "avg_weight": 200.0, "feeding_rate": 2.0}
