import os
import time
import json
import joblib
import requests
import datetime
import pandas as pd
import streamlit as st
import sqlite3

# استيراد مكتبة PDF القياسية
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(interval=0, limit=None, key=None): return None

# استيراد الدوال من ملف db.py بأمان
try:
    from db import insert_data, save_fish_settings, load_latest_fish_settings
except ImportError:
    def insert_data(data): pass
    def save_fish_settings(c, w, r): pass
    def load_latest_fish_settings(): return {"fish_count": 100, "avg_weight": 200.0, "feeding_rate": 2.0}

def get_history(limit=50):
    try:
        conn = sqlite3.connect("aquaponics.db", timeout=10) # إضافة timeout لتفادي قفل قاعدة البيانات أثناء المحاكاة
        query = "SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?"
        df = pd.read_sql(query, conn, params=(limit,))
        conn.close()
        return df.iloc[::-1]
    except:
        return pd.DataFrame()

# تحميل الموديلات بكفاءة
@st.cache_resource
def load_models():
    models = {"plant": None, "fish": None}
    try: models["plant"] = joblib.load("plant_health_model.pkl")
    except: pass
    try: models["fish"] = joblib.load("fish_health_model.pkl")
    except: pass
    return models

models = load_models()
plant_model = models["plant"]
fish_model = models["fish"]

# الإعدادات الصارمة والربط الحقيقي
TELEGRAM_TOKEN = "8976549075:AAEXwqK80xq4rxxeYUA8bNRYmSQ6_GUdNJ8"
TELEGRAM_CHAT_ID = "6186455351" 

st.set_page_config(page_title="Aquaponics IoT Decision Center", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.main { background: #0b1220; color: #ffffff; }
div[data-testid="metric-container"] { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); padding: 14px; border-radius: 14px; }
.stButton button { background: linear-gradient(90deg,#2563eb,#1d4ed8); color: white; border-radius: 10px; font-weight: bold; }
h1, h2, h3 { color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# 🔥 التحديث التلقائي الآمن كل 4 ثوانٍ ليفك تجميد الشاشة تماماً ويتوافق مع السيميوليشن
st_autorefresh(interval=4000, key="iot_refresh")
fish_data = load_latest_fish_settings()

# 🔥 الحل الهندسي السحري لفك التجميد وثبات الأرقام: قراءة ملف الـ JSON الحي المحدث بالملي ثانية من المحاكاة
try:
    if os.path.exists("live_data.json"):
        with open("live_data.json", "r", encoding="utf-8") as f:
            s_data = json.load(f)
    else:
        raise FileNotFoundError
except Exception:
    # قيم افتراضية حية وآمنة للرجوع إليها في حال لم تكن المحاكاة تعمل بعد
    s_data = {
        "water_temp": 26.5, "ph": 7.3, "oxygen": 7.8, "humidity": 45.0, "air_temp": 24.5, "water_level": 70.0,
        "ammonia": 0.12, "nitrite": 0.02, "nitrate": 15.4, "flow_rate": 1.25
    }

# القراءات الحية المتزامنة 100% والمتحركة تلقائياً بناءً على ملف الـ JSON المشترك
water_temp  = float(s_data.get("water_temp", 26.5))
ph          = float(s_data.get("ph", 7.3))
oxygen      = float(s_data.get("oxygen", 7.8))
humidity    = float(s_data.get("humidity", 45.0))
air_temp    = float(s_data.get("air_temp", 24.5))
water_level = float(s_data.get("water_level", 70.0))

ammonia     = float(s_data.get("ammonia", 0.12))
nitrite     = float(s_data.get("nitrite", 0.02))
nitrate     = float(s_data.get("nitrate", 15.4))
flow_rate   = float(s_data.get("flow_rate", 1.25))

# التحقق من سلامة الحساسات
sensor_status = {
    "water_temp": 0 < water_temp < 60,
    "ph": 0 < ph < 14,
    "oxygen": 0 < oxygen < 30,
    "humidity": 0 <= humidity <= 100,
    "air_temp": -20 < air_temp < 70,
    "water_level": 0 <= water_level <= 100
}
failed_sensors = [sensor for sensor, status in sensor_status.items() if not status]

pump_failure = flow_rate < 0.5
water_leak = water_level < 20
# 🔥 تصحيح: تعريف القيمة الابتدائية لسكور الصيانة أولاً قبل تطبيق الشروط لمنع الـ NameError
maintenance_score = 100

if flow_rate < 1: 
    maintenance_score -= 25

if oxygen < 5: 
    maintenance_score -= 20

if water_level < 20: 
    maintenance_score -= 15

# التأكد من أن السكور لا ينزل تحت الصفر
maintenance_score = max(maintenance_score, 0)


# حساب سكور جودة المياه العام
score = 100
reasons = []
if oxygen < 5: reasons.append("Low oxygen"); score -= 25
if water_temp > 30: reasons.append("High water temp"); score -= 15
if ph < 6 or ph > 8: reasons.append("pH chemical instability"); score -= 15
if water_level < 20: reasons.append("Low tank water level"); score -= 20
score = max(score, 0)

if oxygen < 5 or water_temp > 32 or water_level < 20: mode = "🔴 CRITICAL"
elif ph < 6 or ph > 8 or score < 80: mode = "🟡 WARNING"
else: mode = "🟢 OPTIMAL"

# محرك استنتاج سكور التغذية ورسائل التلغرام الحية
total_biomass_g = fish_data["fish_count"] * fish_data["avg_weight"]
total_biomass_kg = total_biomass_g / 1000.0
ideal_feed_g = total_biomass_g * (fish_data["feeding_rate"] / 100.0)

if "actual_feed_input" not in st.session_state:
    st.session_state["actual_feed_input"] = float(round(ideal_feed_g, 1))

feeding_score = 100
feeding_analysis_notes = []
feed_deviation_pct = ((st.session_state["actual_feed_input"] - ideal_feed_g) / ideal_feed_g) * 100.0 if ideal_feed_g > 0 else 0

if feed_deviation_pct > 15:
    feeding_score -= min(int(feed_deviation_pct), 40)
    feeding_analysis_notes.append(f"⚠️ الإفراط في التغذية (+{round(feed_deviation_pct, 1)}%). خطر تراكم العلف وتحلله.")
elif feed_deviation_pct < -15:
    feeding_score -= min(int(abs(feed_deviation_pct)), 40)
    feeding_analysis_notes.append(f"⚠️ نقص في التغذية ({round(feed_deviation_pct, 1)}%). قد يتباطأ النمو.")
else:
    feeding_analysis_notes.append("✅ كمية الغذاء المضافة متطابقة تماماً مع متطلبات الكتلة الحيوية.")

if ammonia > 0.5:
    feeding_score -= 30
    feeding_analysis_notes.append("❌ ارتفاع نسبة الأمونيا السامة في الحوض!")
if oxygen < 5.0:
    feeding_score -= 15
    feeding_analysis_notes.append("⚠️ انخفاض الأكسجين المذاب يقلل كفاءة الهضم.")

feeding_score = max(min(feeding_score, 100), 0)

recommendations = []
if oxygen < 5: recommendations.append("Increase aeration immediately.")
if ammonia > 0.5: recommendations.append("Reduce feeding and inspect biofilter.")
if water_level < 20: recommendations.append("Refill tank and inspect leakage.")
if ph < 6: recommendations.append("Add alkaline buffer.")
if ph > 8: recommendations.append("Lower pH gradually.")

# حفظ البيانات تلقائياً في قاعدة البيانات بأمان تام من التضارب
try:
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_data((current_time, water_temp, ph, oxygen, humidity, air_temp, water_level, ammonia, nitrite, nitrate, flow_rate))
except: 
    pass

# ==========================================
# دالة صناعة تقرير الـ PDF المدمجة
# ==========================================
def build_pdf_report():
    filename = "Aquaponics_Live_Report.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, textColor=colors.HexColor('#1d4ed8'), spaceAfter=12)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=16, textColor=colors.HexColor('#0f172a'), spaceAfter=8)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=14, spaceAfter=6)
    
    story.append(Paragraph("Aquaponics System Automated Analytical Report", title_style))
    story.append(Paragraph(f"Generated Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("1. Real-time Water & Environmental Telemetry", header_style))
    sensor_data_table = [
        ["Parameter", "Current Value", "Parameter", "Current Value"],
        ["Water Temp", f"{water_temp} C", "Air Humidity", f"{humidity} %"],
        ["Water pH Level", f"{ph}", "Air Temp", f"{air_temp} C"],
        ["Dissolved O2", f"{oxygen} mg/L", "Water Tank Level", f"{water_level} %"],
        ["Ammonia (NH3)", f"{ammonia} ppm", "Water Tank Flow", f"{flow_rate} L/min"]
    ]
    t1 = Table(sensor_data_table)
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#e2e8f0'))
    ]))
    story.append(t1)
    story.append(Spacer(1, 15))
    story.append(Paragraph("2. Fish Stocking & Feeding Assessment", header_style))
    story.append(Paragraph(f"<b>Total Fish Count:</b> {fish_data['fish_count']} | <b>FEEDING MANAGEMENT SCORE:</b> {feeding_score} / 100", body_style))
    
    doc.build(story)
    return filename

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ IoT Control Center")
    st.metric("System Health Mode", mode)
    st.metric("Global Ecosystem Score", f"{score}/100")
    st.info("💡 Real-time Sync Active (وضع التزامن الحقيقي المتكامل)")

# --- MAIN ALERTS ---
if feeding_score >= 85 and score >= 85:
    st.success(f"🌟 المنظومة البيئية مستقرة تماماً ومثالية! سكور التغذية الحالية: {feeding_score}% وصحة النظام الإجمالية ممتازة.")
elif feeding_score < 70 or "CRITICAL" in mode:
    st.error(f"⚠️ انتباه: يوجد خلل تشغيلي حرج! سكور إدارة التغذية انخفض إلى {feeding_score}%. يرجى مراجعة كميات العلف فوراً.")
else:
    st.warning("⚠️ النظام في وضع التحذير المعتدل. يرجى مراقبة جودة الفلترة الحيوية ومستويات النيترات.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard & Trends", 
    "🤖 Deep Analytics & AI", 
    "🐟 Fish Feeding Optimization", 
    "📄 Reports Engine"
])

# ==========================================
# --- TAB 1: DASHBOARD & TRENDS ---
# ==========================================
with tab1:
    c1, c2, c3 = st.columns(3)
    c1.metric("🌡 Water Temp", f"{water_temp} °C")
    c2.metric("🧪 pH Level", ph)
    c3.metric("🫧 Dissolved O2", f"{oxygen} mg/L")
    
    # توزيع مؤشرات البيئة والمحيط
    c4, c5, c6 = st.columns(3)
    c4.metric("💧 Air Humidity", f"{humidity} %")
    c5.metric("🌬 Air Temp", f"{air_temp} °C")
    c6.metric("🚰 Water Level", f"{water_level} %")

    st.divider()

    # شارتات تاريخية متحركة ومسحوبة تلقائياً من قاعدة البيانات
    st.markdown("### 📈 Historical Ecosystem Analytics")
    df_history = get_history(limit=30)
    if not df_history.empty:
        if "time" in df_history.columns:
            df_history = df_history.set_index("time")
            
        ch1, ch2 = st.columns(2)
        with ch1:
            st.markdown("##### 🌡️ Water Temperature & Oxygen Trends")
            available_cols = [col for col in ["water_temp", "oxygen"] if col in df_history.columns]
            if available_cols:
                st.line_chart(df_history[available_cols])
        with ch2:
            st.markdown("##### 🧪 pH Stability Trend")
            if "ph" in df_history.columns:
                st.line_chart(df_history["ph"])
    else:
        st.info("💡 جاري تجميع البيانات التاريخية ورسم الشارتات الحية...")

# ==========================================
# --- TAB 2: DEEP ANALYTICS & AI ---
# ==========================================
with tab2:
    st.markdown("### 🌱 Plant Health Intelligence (توقعات صحة النبات الذكية)")

    if plant_model is not None:
        try:
            # تغذية الموديل بالقيم المحدثة
            plant_pred = plant_model.predict(pd.DataFrame([[ph, nitrate, humidity, air_temp]], columns=["ph", "nitrate", "humidity", "air_temp"]))
            st.success(f"🍀 Plant Health Prediction: **{plant_pred[0]}**")
        except Exception as e:
            st.warning(f"ML Prediction Error: {str(e)}")
    else:
        st.error("❌ Plant ML Model file is offline. (ملف الذكاء الاصطناعي للنبات غير متصل)")

    st.divider()
    col_an1, col_an2 = st.columns(2)
    with col_an1:
        st.markdown("### 🧬 Ecosystem Balance Analysis (التوازن البيولوجي)")
        bio_ratio = round((fish_data["fish_count"] / nitrate) if nitrate > 0 else 0, 2)
        st.write(f"**Fish-to-Nitrate Ratio:** {bio_ratio}")
        
        if bio_ratio > 15:
            st.error("⚠️ كثافة سمكية زائدة! الفلتر الحيوي لا يستطيع تحويل الأمونيا إلى نيترات بالسرعة الكافية لاستيعاب الفضلات.")
        elif bio_ratio < 3:
            st.warning("⚠️ نقص مغذيات حاد! مستوى النيترات منخفض جداً مما يهدد النباتات بالجوع لنقص الأسماك.")
        else:
            st.success("✅ التوازن البيولوجي مثالي: دورة النيتروجين الناتجة من البكتيريا تتطابق تماماً مع امتصاص النباتات.")

    with col_an2:
        st.markdown("### 🔮 AI Model Inferences (تنبؤات صحة القطيع السمكي)")
        if fish_model is not None:
            try:
                # موديول الأسماك المصحح والمتوافق مع الأعمدة الثلاثة لحسابك
                fish_pred = fish_model.predict(pd.DataFrame([[water_temp, ph, oxygen]], columns=['water_temp', 'ph', 'oxygen']))
                st.info(f"🐟 Fish Stress Model Prediction: **{fish_pred[0]}**")
            except Exception as e:
                st.warning(f"Fish Model Error: {str(e)}")
        else:
            st.error("❌ Fish ML Model file is offline. (ملف الذكاء الاصطناعي للأسماك غير متصل)")

        # التنبؤ بالساعة القادمة عبر المحاكاة
        predicted_temp = round(water_temp + 0.3, 1)
        predicted_ph = round(ph + 0.1, 2)
        predicted_oxygen = round(oxygen - 0.2, 2)

        st.markdown("##### 🔮 Next Hour Forecast (توقعات الساعة القادمة)")
        f1, f2, f3 = st.columns(3)
        f1.metric("Future Temp", f"{predicted_temp} °C")
        f2.metric("Future pH", predicted_ph)
        f3.metric("Future O₂", f"{predicted_oxygen} mg/L")

    st.divider()
    st.markdown("### 📋 Smart Corrective Actions (الإجراءات التصحيحية الذكية)")
    if recommendations:
        for rec in recommendations:
            st.info(rec)
    else:
        st.success("✅ No corrective actions required. All systems operational.")

# ==========================================
# --- TAB 3: FISH FEEDING OPTIMIZATION ---
# ==========================================
with tab3:
    st.markdown("### 🐟 حاسبة التغذية والسماد الذكية (Biomass & Feeding Optimization)")
    st.write("قم بتحديث بيانات الحوض الحالية ليقوم النظام بحساب الاحتياجات البيولوجية الدقيقة فوراً ومقارنتها بالمحاكاة:")

    # مدخلات تعديل حجم الأسماك ومعدلاتها الحية
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1:
        fish_count_input = st.number_input("🔢 عدد الأسماك في الحوض (Fish Count):", min_value=1, value=int(fish_data.get("fish_count", 100)), step=10)
    with col_input2:
        avg_weight_input = st.number_input("⚖️ متوسط وزن السمكة الواحدة (جرام):", min_value=1.0, value=float(fish_data.get("avg_weight", 200.0)), step=5.0)
    with col_input3:
        feeding_rate_input = st.number_input("📊 معدل التغذية اليومي (% من وزن الجسم):", min_value=0.5, max_value=10.0, value=float(fish_data.get("feeding_rate", 2.0)), step=0.5)

    st.markdown("##### 🌿 إدارة المغذيات والتقوية (Fertilizer & Supplement Input)")
    col_fer1, col_fer2 = st.columns(2)
    with col_fer1:
        fertilizer_added = st.number_input("🧪 كمية السماد/المكمل المضافة حالياً (مليجرام/لتر):", min_value=0.0, value=0.0, step=0.5)
    with col_fer2:
        actual_feed = st.number_input("🍽️ كمية العلف المضافة فعلياً للحوض (جرام):", min_value=0.0, value=float(st.session_state["actual_feed_input"]), step=5.0)
        st.session_state["actual_feed_input"] = actual_feed

    # إعادة الحسابات الميدانية ديناميكياً
    calculated_biomass_g = fish_count_input * avg_weight_input
    calculated_biomass_kg = calculated_biomass_g / 1000.0
    dynamic_ideal_feed_g = calculated_biomass_g * (feeding_rate_input / 100.0)
    dynamic_deviation_pct = ((actual_feed - dynamic_ideal_feed_g) / dynamic_ideal_feed_g) * 100.0 if dynamic_ideal_feed_g > 0 else 0

    st.divider()
    st.markdown("#### 📊 نتائج التحليل الحي ومطابقة العلف:")
    res1, res2, res3 = st.columns(3)
    res1.metric("⚖️ الكتلة الحيوية الإجمالية", f"{calculated_biomass_kg:.2f} كجم")
    res2.metric("🎯 كمية العلف المثالية المطلوبة", f"{dynamic_ideal_feed_g:.1f} جرام")
    
    if abs(dynamic_deviation_pct) <= 15:
        res3.metric("📢 حالة كمية العلف حالياً", "✅ متطابقة ومثالية", delta=f"{dynamic_deviation_pct:.1f}%")
    elif dynamic_deviation_pct > 15:
        res3.metric("📢 حالة كمية العلف حالياً", "🚨 زيادة (إفراط في التغذية)", delta=f"+{dynamic_deviation_pct:.1f}%", delta_color="inverse")
    else:
        res3.metric("📢 حالة كمية العلف حالياً", "⚠️ نقص (تغذية غير كافية)", delta=f"{dynamic_deviation_pct:.1f}%", delta_color="inverse")

    st.markdown("#### 🔬 تقييم التوازن الكيميائي والسماد (Fertilizer Assessment):")
    total_nitrogen_load = nitrate + (fertilizer_added * 1.5)
    if total_nitrogen_load > 80:
        st.error(f"❌ خطر سمية حاد! مستوى النيترات الحالي ({nitrate} ppm) بالإضافة إلى السماد يتجاوز الحد الآمن للنبات والسمك.")
    elif total_nitrogen_load < 10:
        st.warning(f"⚠️ نقص مغذيات! كمية النيترات الحالية ضعيفة والسماد المضاف غير كافٍ لدعم نمو خضري كثيف للنباتات.")
    else:
        st.success(f"✅ بيئة المغذيات مستقرة وممتازة! (إجمالي الحمل المغذي: {total_nitrogen_load:.1f}).")

    if st.button("💾 حفظ الإعدادات الحالية وتعميمها على نظام المحاكاة"):
        try:
            save_fish_settings(fish_count_input, avg_weight_input, feeding_rate_input)
            st.success("🔄 تم حفظ الإعدادات بنجاح وتحديث قاعدة البيانات الموحدة!")
        except Exception as e:
            st.error(f"فشل حفظ الإعدادات: {str(e)}")

# ==============================================
# --- TAB 4: REPORTS ENGINE ---
# ==========================================
with tab4:
    st.markdown("### 📄 Automated PDF Report Generator (محرك التقارير الهندسية)")
    st.write("اضغط على الزر أدناه لتوليد وتحميل تقرير تحليلي شامل ومطبوع يعكس البيانات اللحظية المشتركة الحالية:")
    
    if REPORTLAB_AVAILABLE:
        if st.button("Build Latest System Report"):
            try:
                # توليد الملف
                pdf_file = build_pdf_report()
                
                # فتح وتهيئة زر التحميل للمتصفح
                with open(pdf_file, "rb") as f:
                    st.download_button(
                        label="📥 Download PDF Report", 
                        data=f, 
                        file_name=pdf_file, 
                        mime="application/pdf"
                    )
                st.success("🏆 Report generated successfully! Click the button above to save your copy.")
            except Exception as e:
                st.error(f"❌ Failed to build PDF Report: {str(e)}")
    else:
        st.error("❌ ReportLab library is missing. Cannot generate PDF reports.")
