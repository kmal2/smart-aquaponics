import streamlit as st
import pandas as pd
import time
import importlib

# استيراد أداة التحديث التلقائي، وإذا لم تكن مثبتة نستخدم بديل آمن
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(interval=0, limit=None, key=None): return None

st.set_page_config(page_title="Smart Aquaponics AI Dashboard", layout="wide")

st.title("🌱 Smart Aquaponics AI Dashboard")

# 1. التحديث التلقائي الآمن كل 4 ثوانٍ ليتوافق مع سرعة ضخ المحاكاة (بديل الـ while True القاتل)
st_autorefresh(interval=4000, key="aquaponics_refresh")

# 2. إدارة البيانات التاريخية بأمان في الـ session_state لمنع انفجار الذاكرة
if "history" not in st.session_state:
    st.session_state.history = []

# 3. قراءة البيانات الحقيقية والموحدة من ملف الذاكرة المشتركة الحية
try:
    import shared_data
    # إعادة تحميل الموديول إجبارياً برمجياً ليرى الأرقام الجديدة التي يكتبها المحاكي في نفس الثانية
    importlib.reload(shared_data)
    data = shared_data.DATA
except Exception as e:
    # قيم افتراضية آمنة في حال لم تكن المحاكاة تعمل بعد
    data = {
        "water_temp": 25.0, "ph": 7.2, "oxygen": 7.5,
        "humidity": 50.0, "air_temp": 24.0, "water_level": 70.0
    }

# 4. محرك الاستنتاج والذكاء الاصطناعي التشغيلي (AI logic)
def ai_control(current_data):
    alert = []
    if current_data.get("oxygen", 0) < 5:
        alert.append("⚠️ Low Oxygen Detected (انخفاض حاد في الأكسجين المذاب)")
    if current_data.get("water_temp", 0) > 30:
        alert.append("⚠️ High Water Temperature (ارتفاع خطر لدرجة حرارة المياه)")
    if current_data.get("ph", 0) < 6 or current_data.get("ph", 0) > 8:
        alert.append("⚠️ pH Out of Range (عدم استقرار كيميائي في مستوى الـ pH)")
    return alert

alerts = ai_control(data)

# 5. إضافة القراءة الحالية للقائمة التاريخية مع الحفاظ على حد أقصى (آخر 30 قراءة فقط) لحماية الذاكرة
st.session_state.history.append(data)
if len(st.session_state.history) > 30:
    st.session_state.history.pop(0) # حذف أقدم قراءة للحفاظ على رشاقة المتصفح

# تحويل التاريخ إلى DataFrame للرسم البياني
df = pd.DataFrame(st.session_state.history)

# --- بناء الواجهة الرسومية (UI Layout) ---
# عرض المؤشرات الرقمية الحية (Metrics)
col1, col2, col3 = st.columns(3)
col1.metric("🌡️ Water Temp", f"{data.get('water_temp'):.2f} °C")
col2.metric("🧪 pH Level", f"{data.get('ph'):.2f}")
col3.metric("🫧 Dissolved Oxygen", f"{data.get('oxygen'):.2f} mg/L")

st.divider()

# عرض التنبيهات والتحليلات الذكية
st.subheader("🤖 AI Real-time Alerts")
if len(alerts) == 0:
    st.success("System Stable 🟢 (جميع المؤشرات الحيوية مستقرة تماماً)")
else:
    for alert_msg in alerts:
        st.error(alert_msg)

st.divider()

# عرض الرسومات البيانية التاريخية المتزامنة
st.subheader("📊 Live Trends (Last 30 Readings)")
if not df.empty:
    # التحقق من وجود الأعمدة المطلوبة لتجنب أي خطأ في الرسم
    available_cols = [col for col in ["water_temp", "ph", "oxygen"] if col in df.columns]
    if available_cols:
        st.line_chart(df[available_cols])
