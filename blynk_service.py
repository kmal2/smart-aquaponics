import requests
import random
import time
import os
import json

BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"

# 🔥 تصحيح: استخدام المسار الصحيح والمباشر لـ Blynk API المجمع
BLYNK_URL = "https://blynk.cloud"

def save_and_broadcast_data(data):
    """
    تحديث ملف shared_data.py برمجياً على القرص الصلب لضمان قيام 
    تطبيق Streamlit بقراءته حياً وتطابق النتائج 100% بين الشاشتين
    """
    try:
        content = f"""import time

DATA = {json.dumps(data, indent=4)}
"""
        with open("shared_data.py", "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print("🚨 Error writing shared_data file:", e)

def send_all_to_blynk_batch(data_dict):
    """
    🔥 تعديل هندسي جوهري: إرسال جميع القراءات الستة في طلب HTTP واحد مجمع 
    (Batch Update) لتفادي الـ Lag والحظر، وتحديث السحابة بالملي ثانية
    """
    try:
        # صياغة الـ Parameters للطلب المجمع في Blynk API
        params = {
            "token": BLYNK_AUTH,
            "V0": f"{data_dict['water_temp']:.2f}",
            "V1": f"{data_dict['ph']:.2f}",
            "V2": f"{data_dict['oxygen']:.2f}",
            "V3": f"{data_dict['humidity']:.2f}",
            "V4": f"{data_dict['air_temp']:.2f}",
            "V5": f"{data_dict['water_level']:.2f}"
        }
        # إرسال طلب واحد مجمع وبوقت انتظار سريع
        response = requests.get(BLYNK_URL, params=params, timeout=2.0)
        return response.status_code == 200
    except:
        return False

print("🚀 Blynk & Streamlit Dynamic Twin Simulation Service Running...")

while True:
    # 1. توليد القراءات الديناميكية والمحاكاة الحية
    current_data = {
        "water_temp": round(random.uniform(26.5, 28.5), 2),
        "ph": round(random.uniform(7.1, 7.6), 2),
        "oxygen": round(random.uniform(7.5, 8.5), 2),
        "humidity": round(random.uniform(38.0, 42.0), 2),
        "air_temp": round(random.uniform(24.5, 26.5), 2),
        "water_level": round(random.uniform(54.0, 58.0), 2),
        "ammonia": round(random.uniform(0.1, 0.2), 2),
        "nitrite": round(random.uniform(0.01, 0.03), 3),
        "nitrate": round(random.uniform(12.0, 16.0), 1),
        "flow_rate": round(random.uniform(1.1, 1.3), 2),
        "timestamp": time.time()
    }

    # 2. بث البيانات وتحديث ملف الذاكرة المشتركة الحية على القرص ليتزامن مع Streamlit فوراً
    save_and_broadcast_data(current_data)

    # 3. ضخ القراءات للسحابة بطلب واحد فائق السرعة
    success = send_all_to_blynk_batch(current_data)
    
    if success:
        print(f"📡 [SUCCESS] Batch Pushed to Blynk -> Temp: {current_data['water_temp']} | pH: {current_data['ph']}")
    else:
        print(f"⚠️ [WARNING] Blynk Batch Push Failed or Delayed -> Temp: {current_data['water_temp']}")

    # دورة التحديث المستقرة كل 4 ثوانٍ
    time.sleep(4)
