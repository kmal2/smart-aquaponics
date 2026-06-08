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
    إرسال تقارير هندسية متكاملة لـ Telegram مع تفعيل حماية صارمة لمنع حظر البوت
    """
    global last_telegram_time, last_alert_status
    
    reasons = []
    actions = []
    
    if data_dict["oxygen"] < 5.5: 
        reasons.append(f"❌ انخفاض حرج للأكسجين المذاب: {data_dict['oxygen']} mg/L")
        actions.append("⚡ [إجراء فوري]: تشغيل مضخة التهوية الاحتياطية بكامل طاقتها.")
        
    if data_dict["water_temp"] > 28.5: 
        reasons.append(f"❌ ارتفاع حرارة المياه: {data_dict['water_temp']}°C")
        actions.append("⚡ [إجراء فوري]: تفعيل نظام التبريد الجبري (Chiller System).")
    elif data_dict["water_temp"] < 23.0:
        reasons.append(f"❌ انخفاض حرارة المياه: {data_dict['water_temp']}°C")
        actions.append("⚡ [إجراء فوري]: تشغيل السخانات الرقمية المتكاملة.")

    if data_dict["ph"] < 6.5: 
        reasons.append(f"❌ حموضة مرتفعة بالماء pH: {data_dict['ph']}")
        actions.append("⚡ [إجراء فوري]: إضافة منظم قلوي (Alkaline Buffer) تدريجياً.")
    elif data_dict["ph"] > 7.9:
        reasons.append(f"❌ قلوية زائدة بالماء pH: {data_dict['ph']}")
        actions.append("⚡ [إجراء فوري]: حقن كمية مقننة من حامض الفوسفوريك المخفف.")

    if data_dict["water_level"] < 40.0:
        reasons.append(f"❌ انخفاض منسوب المياه بالحوض: {data_dict['water_level']}%")
        actions.append("⚡ [إجراء فوري]: فتح محبس التغذية الآلي لتعويض النقص.")

    current_time = time.time()
    
    if reasons:
        status_msg = "CRITICAL"
        # 🛡️ فلتر مكافحة الحظر (Anti-Spam): لا يرسل إلا إذا مر دقيقة كاملة (60 ثانية) على الأقل على آخر رسالة
        if (current_time - last_telegram_time > 60):
            
            report_text = (
                f"📋 <b><u>تقرير تشخيصي حي: نظام الاستزراع الذكي</u></b>\n\n"
                f"⏰ <b>توقيت الرصد:</b> {time.strftime('%H:%M:%S')}\n"
                f"📊 <b>حالة المنظومة:</b> 🚨 وضع حرج (CRITICAL)\n\n"
                f"🔍 <b>المشاكل المرصودة:</b>\n" + "\n".join(reasons) + "\n\n"
                f"🛠️ <b>القرارات التشغيلية والتدخل الآلي:</b>\n" + "\n".join(actions) + "\n\n"
                f"📌 <i>يرجى المتابعة والتحقق من شاشة التحكم الرئيسية للمشروع.</i>"
            )
            
            try:
                telegram_url = "https://telegram.org"
                res = requests.post(telegram_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": report_text, "parse_mode": "HTML"}, timeout=4)
                
                # فحص حقيقي للتأكد من موافقة سيرفر تلغرام على التوصيل
                if res.status_code == 200:
                    last_telegram_time = current_time
                    last_alert_status = status_msg
                    print("📲 [TELEGRAM] Success! Diagnostic report delivered to your phone.")
                else:
                    print(f"⚠️ [TELEGRAM WARNING] Server received the request but blocked delivery (Rate Limit Active). Code: {res.status_code}")
            except Exception as e:
                print("🚨 Telegram Exception:", e)
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
