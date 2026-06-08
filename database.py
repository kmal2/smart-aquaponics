import sqlite3
import datetime

DB_NAME = "aquaponics.db"

def init_database():
    """إنشاء الجدول بالهيكل المطور والكامل إذا لم يكن موجوداً"""
    # فتح الاتصال وإغلاقه داخل الدالة يمنع تماماً أخطاء الـ Threading وقفل قاعدة البيانات
    conn = sqlite3.connect(DB_NAME, timeout=10)
    try:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            time TEXT,
            water_temp REAL,
            ph REAL,
            oxygen REAL,
            humidity REAL,
            air_temp REAL,
            water_level REAL,
            ammonia REAL,
            nitrite REAL,
            nitrate REAL,
            flow_rate REAL
        )
        """)
        conn.commit()
    except Exception as e:
        print("🚨 [DB ERROR] Initialization Failed:", e)
    finally:
        conn.close()

# استدعاء دالة التهيئة فوراً عند قراءة الملف للتأكد من جاهزية الجدول
init_database()

def save_data(data):
    """حفظ بيانات الحساسات اللحظية بأمان تام من أي خيط برمي (Thread-Safe)"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    try:
        cursor = conn.cursor()
        
        # التقاط التوقيت الحالي بدقة إذا لم يكن ممرراً من المحاكاة
        current_time = data.get("time", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        cursor.execute("""
        INSERT INTO sensor_data (
            time, water_temp, ph, oxygen, humidity, air_temp, 
            water_level, ammonia, nitrite, nitrate, flow_rate
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            current_time,
            data.get("water_temp", 0.0),
            data.get("ph", 0.0),
            data.get("oxygen", 0.0),
            data.get("humidity", 0.0),
            data.get("air_temp", 0.0),
            data.get("water_level", 0.0),
            data.get("ammonia", 0.0),
            data.get("nitrite", 0.0),
            data.get("nitrate", 0.0),
            data.get("flow_rate", 0.0)
        ))
        conn.commit()
    except Exception as e:
        print("🚨 [DB ERROR] Save Data Failed:", e)
    finally:
        conn.close()

def get_data(limit=50):
    """قراءة البيانات التاريخية بشكل آمن ومنظم لخدمة الشارتات الرسومية في الواجهة"""
    conn = sqlite3.connect(DB_NAME, timeout=10)
    try:
        cursor = conn.cursor()
        # جلب آخر البيانات المضافة لترتيبها تاريخياً في الرسومات البيانية
        cursor.execute("SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        print("🚨 [DB ERROR] Read Data Failed:", e)
        return []
    finally:
        conn.close()
