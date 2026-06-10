import requests
import random
import time
import json
import os

BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"
TELEGRAM_TOKEN = "8976549075:AAEXwqK80xq4rxxeYUA8bNRYmSQ6_GUdNJ8"
TELEGRAM_CHAT_ID = "6186455351"

# ذاكرة مكافحة الحظر ومنع الإغراق المتتالي لرسائل التلغرام
last_telegram_time = 0
last_alert_status = "OK"

def generate_sensor_data():
    """توليد البيانات الحية"""
    return {
        "water_temp": round(random.uniform(22.0, 31.0), 2),
        "ph": round(random.uniform(6.2, 8.2), 2),
        "oxygen": round(random.uniform(4.0, 9.0), 2),
        "humidity": round(random.uniform(45.0, 75.0), 2),
        "air_temp": round(random.uniform(23.0, 32.0), 2),
        "water_level": round(random.uniform(15.0, 95.0), 2),
        "ammonia": round(random.uniform(0.1, 0.6), 2),
        "nitrite": round(random.uniform(0.01, 0.03), 3),
        "nitrate": round(random.uniform(12.0, 16.0), 1),
        "flow_rate": round(random.uniform(0.4, 1.3), 2),
        "timestamp": time.time()
    }

def save_and_broadcast_data(data):
    """تحديث ملف الـ JSON الموحد لستريم ليت فوراً"""
    try:
        with open("live_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("🚨 [ERROR] Cannot write live_data.json:", e)
def send_to_blynk_forced(pin, value):
    """
    🔥 النسخة الاستشارية النهائية لكسر تجميد Blynk: 
    يقوم بايثون بتجربة السيرفرات الإقليمية الثلاثة الرسمية للسحابة تلقائياً 
    حتى يجد السيرفر المطابق لحسابك ويضخ البيانات فوراً
    """
    # قائمة السيرفرات الإقليمية الرسمية لـ Blynk Cloud
    blynk_servers = [
        "https://blynk.cloud",  # السيرفر الأمريكي (الأكثر استخداماً)
        "https://blynk.cloud", # السيرفر الأوروبي
        "https://blynk.cloud", # السيرفر الآسيوي
        "https://blynk.cloud"       # السيرفر العام
    ]
    
    for base_url in blynk_servers:
        try:
            # صياغة الرابط القياسي المضمون للـ Virtual Pins
            url = f"{base_url}/external/api/update?token={BLYNK_AUTH}&{pin}={value}"
            res = requests.get(url, timeout=1.0) # وقت انتظار سريع للتنقل
            
            # بمجرد أن يرد السيرفر الصحيح بـ 200 ينجح الإرسال فوراً
            if res.status_code == 200:
                return True
        except:
            continue # إذا فشل سيرفر ينتقل للتالي فوراً بدون كراش
            
    return False

def check_and_send_telegram_report(data_dict):
    """
    إرسال تقارير هندسية تملك مصفوفة الأرقام بالكامل والتفاصيل الحيوية لهاتفك
    """
    global last_telegram_time, last_alert_status
    
    reasons = []
    actions = []
    
    if data_dict["oxygen"] < 5.5: 
        reasons.append(f"❌ انخفاض الأكسجين: <b>{data_dict['oxygen']:.2f} mg/L</b> (الحد الآمن &gt; 5.5)")
        actions.append("⚡ [تدخل فوري]: تشغيل مضخة التهوية الاحتياطية (Aerator Pump 2).")
        
    if data_dict["water_temp"] > 28.5: 
        reasons.append(f"❌ ارتفاع حرارة المياه: <b>{data_dict['water_temp']:.2f} °C</b> (الحد الآمن &lt; 28.5)")
        actions.append("⚡ [تدخل فوري]: تفعيل المبرد الجبري (Chiller System) ومراوح التبريد.")
    elif data_dict["water_temp"] < 23.0:
        reasons.append(f"❌ انخفاض حرارة المياه: <b>{data_dict['water_temp']:.2f} °C</b> (الحد الآمن &gt; 23.0)")
        actions.append("⚡ [تدخل فوري]: تنشيط السخانات الرقمية (Heaters Grid).")

    if data_dict["ammonia"] > 0.3: 
        reasons.append(f"❌ سمية أمونيا حادة: <b>{data_dict['ammonia']:.2f} ppm</b> (الحد الآمن &lt; 0.25)")
        actions.append("⚡ [تدخل فوري]: حظر حاسبة التغذية مؤقتاً لتجنب زيادة التحلل.")

    if data_dict["water_level"] < 40.0:
        reasons.append(f"❌ انخفاض منسوب المياه: <b>{data_dict['water_level']:.2f} %</b> (خطر جفاف)")
        actions.append("⚡ [تدخل فوري]: فتح محبس التغذية الإلكتروني (Solenoid Refill Valve).")

    current_time = time.time()
    
    if reasons:
        status_msg = "CRITICAL"
        # فلتر مكافحة الحظر: يرسل التحديث التفصيلي الرقمي كل 60 ثانية لحمايتك
        if (current_time - last_telegram_time > 60):
            
            # صياغة مصفوفة شاملة للأرقام الحالية في نص الرسالة ليراها المستخدم
            report_text = (
                f"📋 <b><u>تقرير القياس التشخيصي الموحد (Telemetry Run)</u></b>\n\n"
                f"⏰ <b>توقيت الرصد:</b> {time.strftime('%H:%M:%S')}\n"
                f"📊 <b>حالة النظام الكلية:</b> 🚨 وضع حرج (CRITICAL)\n\n"
                f"📈 <b>مصفوفة الأرقام اللحظية للحساسات:</b>\n"
                f"- حرارة المياه: {data_dict['water_temp']:.2f} °C\n"
                f"- مستوى الـ pH: {data_dict['ph']:.2f}\n"
                f"- الأكسجين المذاب: {data_dict['oxygen']:.2f} mg/L\n"
                f"- منسوب المياه: {data_dict['water_level']:.2f} %\n"
                f"- نسبة الأمونيا: {data_dict['ammonia']:.2f} ppm\n"
                f"- نسبة النيترات: {data_dict['nitrate']:.2f} ppm\n\n"
                f"🔍 <b>المشاكل المرصودة وأسبابها:</b>\n" + "\n".join(reasons) + "\n\n"
                f"🛠️ <b>الأوامر الميدانية والتدخل المطلوب:</b>\n" + "\n".join(actions)
            )
            
            try:
                telegram_url = "https://telegram.org"
                res = requests.post(telegram_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": report_text, "parse_mode": "HTML"}, timeout=4)
                if res.status_code == 200:
                    last_telegram_time = current_time
                    last_alert_status = status_msg
                    print("📲 [TELEGRAM] Detailed technical payload delivered successfully.")
            except Exception as e:
                print("🚨 Telegram Error:", e)
    else:
        last_alert_status = "OK"

# --- المحرك الرئيسي للمنظومة ---
print("==================================================")
print("🚀 Launching Integrated Digital Twin Simulation...")
print("==================================================")

try:
    while True:
        # 1. توليد البيانات العشوائية المتوافقة
        current_data = generate_sensor_data()
        
        # 2. المزامنة والرقمنة اللحظية لـ Streamlit عبر الـ JSON
        save_and_broadcast_data(current_data)
        
        # 3. دفع البيانات لـ Blynk بأبسط صيغة مقبولة برمجياً للـ Virtual Pins
        b0 = send_to_blynk_forced("V0", current_data["water_temp"])
        b1 = send_to_blynk_forced("V1", current_data["ph"])
        b2 = send_to_blynk_forced("V2", current_data["oxygen"])
        b3 = send_to_blynk_forced("V3", current_data["humidity"])
        b4 = send_to_blynk_forced("V4", current_data["air_temp"])
        b5 = send_to_blynk_forced("V5", current_data["water_level"])
        
        # 4. الرصد الفوري وإرسال التقارير لـ Telegram بفلتر مكافحة الحظر
        check_and_send_telegram_report(current_data)
        
        if b0 or b1 or b2:
            print(f"📡 [SUCCESS] Sync Active -> Temp: {current_data['water_temp']}°C | O₂: {current_data['oxygen']} | Time: {time.strftime('%H:%M:%S')}")
        else:
            print("❌ [FAILED] Cloud Sync Delayed. Check Auth Token or Web Dashboard Settings.")
            
        # دورة التحديث المستقرة كل 4 ثوانٍ
        time.sleep(4)
except KeyboardInterrupt:
    print("\n🛑 Simulation stopped.")
