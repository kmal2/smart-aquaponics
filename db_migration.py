import sqlite3

DB_NAME = "aquaponics.db"

# 🔥 تم إضافة عمود الوقت TEXT لضمان وجوده لدعم شارتات ستريم ليت والتقارير
REQUIRED_COLUMNS = {
    "time": "TEXT",
    "ammonia": "REAL",
    "nitrite": "REAL",
    "nitrate": "REAL",
    "flow_rate": "REAL"
}

def migrate_db():
    """تحديث هيكل قاعدة البيانات تلقائياً وإضافة الأعمدة الناقصة بأمان تام"""
    # إضافة timeout لمنع التعارض وقفل قاعدة البيانات أثناء التحديث
    conn = sqlite3.connect(DB_NAME, timeout=10)
    try:
        cursor = conn.cursor()

        # جلب الأعمدة الحالية الموجودة في الجدول فعلياً
        cursor.execute("PRAGMA table_info(sensor_data)")
        existing_cols = [col[1] for col in cursor.fetchall()]

        # فحص وإضافة أي عمود ناقص ديناميكياً دون المساس بالبيانات القديمة
        for col, col_type in REQUIRED_COLUMNS.items():
            if col not in existing_cols:
                print(f"🛠️ Adding missing column: {col} ({col_type})")
                cursor.execute(f"ALTER TABLE sensor_data ADD COLUMN {col} {col_type}")
        
        conn.commit()
        print("✅ Database migration completed successfully (تم تحديث قاعدة البيانات بنجاح)")
        
    except Exception as e:
        print("🚨 [MIGRATION ERROR] Failed to migrate database:", e)
    finally:
        # التأكد من إغلاق الاتصال دائماً لتحرير قاعدة البيانات
        conn.close()

# تنفيذ الهجرة تلقائياً عند استدعاء الملف
if __name__ == "__main__":
    migrate_db()
