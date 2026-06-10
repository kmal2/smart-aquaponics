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
except (ImportError, ModuleNotFoundError):
    letter = None
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    Table = None
    TableStyle = None
    getSampleStyleSheet = None
    ParagraphStyle = None
    colors = None
    REPORTLAB_AVAILABLE = False

try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(interval=0, limit=None, key=None): return None

try:
    from db import insert_data, save_fish_settings, load_latest_fish_settings
except ImportError:
    def insert_data(data): pass
    def save_fish_settings(c, w, r): pass
    def load_latest_fish_settings(): return {"fish_count": 100, "avg_weight": 200.0, "feeding_rate": 2.0}

def get_history(limit=50):
    try:
        conn = sqlite3.connect("aquaponics.db", timeout=10)
        query = "SELECT * FROM sensor_data ORDER BY id DESC LIMIT ?"
        df = pd.read_sql(query, conn, params=(limit,))
        conn.close()
        return df.iloc[::-1]
    except:
        return pd.DataFrame()

# تحميل الموديلات الذكية بكفاءة
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

# الإعدادات الموحدة
TELEGRAM_TOKEN = "8976549075:AAEXwqK80xq4rxxeYUA8bNRYmSQ6_GUdNJ8"
TELEGRAM_CHAT_ID = "6186455351" 

st.set_page_config(page_title="Aqua Mind AI", layout="wide", initial_sidebar_state="expanded")

#  التصميم  
st.markdown(""""
<style>
    @import url('https://googleapis.com');
    
    /* صياغة الخلفية الكلية للمشروع باللون الكحلي الليلي الفخم */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #0b0f19 !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        color: #f8fafc !important;
    }
    .main { background: #0b0f19; }
    
    /* تصميم محاكاة لـ الشريط العلوي الأزرق الممتد المقتبس من صورتك بدقة متناهية */
    .bi-top-ribbon-container {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 25px;
    }
    .bi-ribbon-card {
        flex: 1;
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        border: 1px solid rgba(59, 130, 246, 0.3);
        padding: 14px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
        transition: all 0.3s ease;
    }
    .bi-ribbon-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
        box-shadow: 0 6px 20px rgba(59, 130, 246, 0.3);
    }
    .bi-ribbon-title {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 4px;
    }
    .bi-ribbon-value {
        color: #3b82f6;
        font-size: 22px;
        font-weight: 800;
    }

    /* هندسة الكروت الزجاجية المضيئة بظلال متوهجة تخطف أنظار لجان التحكيم */
    div[data-testid="metric-container"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        padding: 22px !important;
        border-radius: 16px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
        backdrop-filter: blur(8px) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-4px) !important;
        border-color: rgba(59, 130, 246, 0.5) !important;
        box-shadow: 0 12px 40px rgba(37, 99, 235, 0.25) !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-size: 13px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px;
    }
    div[data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 32px !important;
        font-weight: 800 !important;
    }
    
    /* تصميم الأزرار الاحترافية بنظام التوهج اللوني */
    .stButton button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 12px 28px !important;
        border: none !important;
        box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.6) !important;
        transform: translateY(-1px) !important;
    }
    
    /* تخصيص السايد بار ليكون مدمجاً وفخماً */
    section[data-testid="stSidebar"] {
        background-color: #090d16 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    
    /* تنسيق التبويبات الفاخرة (Tabs) لتبدو كلوحة برمجية موحدة */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(15, 23, 42, 0.8);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        background-color: transparent;
        border-radius: 10px;
        color: #64748b;
        font-weight: 700;
        font-size: 14px;
        transition: all 0.2s ease;
        padding: 0 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);
    }
    
    /* تنسيق الجداول لتطابق جودة الصورة بالملي */
    .styled-table {
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 14px;
        background-color: rgba(15, 23, 42, 0.4);
        border-radius: 8px;
        overflow: hidden;
    }
    .styled-table th {
        background-color: #1a446c;
        color: #ffffff;
        text-align: left;
        padding: 12px;
        font-weight: 700;
    }
    .styled-table td {
        padding: 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# التحديث التلقائي الآمن كل 4 ثوانٍ لمزامنة التوأم الرقمي
st_autorefresh(interval=4000, key="iot_refresh")
fish_data = load_latest_fish_settings()

# قراءة قنوات  اللحظية الحقيقية المحدثة من السيميوليشن بدون كاش
try:
    if os.path.exists("live_data.json"):
        with open("live_data.json", "r", encoding="utf-8") as f:
            s_data = json.load(f)
    else:
        raise FileNotFoundError
except Exception:
    s_data = {
        "water_temp": 26.5, "ph": 7.3, "oxygen": 7.8, "humidity": 45.0, "air_temp": 24.5, "water_level": 70.0,
        "ammonia": 0.12, "nitrite": 0.02, "nitrate": 15.4, "flow_rate": 1.25
    }

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

#     جلب البيانات الإحصائية أولاً وتخزينها في DataFrame لعرضها في شريط المؤشرات العلوي (The BI Ribbon)    
df_stats = get_history(limit=50)

sensor_status = {
    "water_temp": 0 < water_temp < 60, "ph": 0 < ph < 14, "oxygen": 0 < oxygen < 30,
    "humidity": 0 <= humidity <= 100, "air_temp": -20 < air_temp < 70, "water_level": 0 <= water_level <= 100
}
failed_sensors = [sensor for sensor, status in sensor_status.items() if not status]

# حساب سكور الصيانة
maintenance_score = 100
if flow_rate < 1: maintenance_score -= 25
if oxygen < 5: maintenance_score -= 20
if water_level < 20: maintenance_score -= 15
maintenance_score = max(maintenance_score, 0)

# حساب سكور جودة المياه العام
score = 100
if oxygen < 5: score -= 25
if water_temp > 30: score -= 15
if ph < 6 or ph > 8: score -= 15
if water_level < 20: score -= 20
score = max(score, 0)

if oxygen < 5 or water_temp > 32 or water_level < 20: mode = "🔴 CRITICAL"
elif ph < 6 or ph > 8 or score < 80: mode = "🟡 WARNING"
else: mode = "🟢 OPTIMAL"

total_biomass_g = fish_data["fish_count"] * fish_data["avg_weight"]
total_biomass_kg = total_biomass_g / 1000.0
ideal_feed_g = total_biomass_g * (fish_data["feeding_rate"] / 100.0)

if "actual_feed_input" not in st.session_state:
    st.session_state["actual_feed_input"] = float(round(ideal_feed_g, 1))

feeding_score = 100
feed_deviation_pct = ((st.session_state["actual_feed_input"] - ideal_feed_g) / ideal_feed_g) * 100.0 if ideal_feed_g > 0 else 0
if feed_deviation_pct > 15 or feed_deviation_pct < -15: feeding_score -= 30
if ammonia > 0.5: feeding_score -= 30

recommendations = []
if oxygen < 5: recommendations.append("Increase aeration immediately.")
if ammonia > 0.5: recommendations.append("Reduce feeding and inspect biofilter.")

# تتابع حفظ البيانات الحقيقية في قاعدة البيانات SQLite لتاريخ التشغيل الفعلي وعرضها في شريط المؤشرات العلوي (The BI Ribbon)   
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
    
    # استدعاء التنسيقات وتجهيز الألوان الأكاديمية
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=22, textColor=colors.HexColor('#1a446c'), spaceAfter=10)
    header_style = ParagraphStyle('Header', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#102a45'), spaceAfter=6)
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, leading=14, spaceAfter=4)
    alert_style = ParagraphStyle('Alert', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor('#b91c1c'), spaceAfter=4)
    
    # 1. عنوان التقرير والتوقيت الزمني
    story.append(Paragraph("<b>📊 Automated Aquaponics System Diagnostic Report</b>", title_style))
    story.append(Paragraph(f"Generated Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", body_style))
    story.append(Spacer(1, 10))
    
    # 2. جدول البيانات اللحظية الشامل
    story.append(Paragraph("<b>1. Real-time Environmental Telemetry Matrix</b>", header_style))
    sensor_data_table = [
        ["System Parameter", "Current Simulation Value", "Operational Target Status"],
        ["Water Temperature", f"{water_temp:.2f} °C", "Optimal: 23 - 28 °C"],
        ["Water pH Level", f"{ph:.2f}", "Optimal: 6.5 - 7.5"],
        ["Dissolved Oxygen (O2)", f"{oxygen:.2f} mg/L", "Optimal: > 5.5 mg/L"],
        ["Atmospheric Humidity", f"{humidity:.2f} %", "Optimal: 40 - 80 %"],
        ["Water Tank Level", f"{water_level:.2f} %", "Optimal: > 50 %"],
        ["Ammonia (NH3) Load", f"{ammonia:.2f} ppm", "Optimal: < 0.25 ppm"],
        ["Nitrate (NO3) Level", f"{nitrate:.2f} ppm", "Optimal: 10 - 40 ppm"],
        ["Hydro-Pump Flow Rate", f"{flow_rate:.2f} L/min", "Optimal: > 1.0 L/min"]
    ]
    t1 = Table(sensor_data_table, colWidths=[200, 150, 200])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a446c')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8fafc')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t1)
    story.append(Spacer(1, 12))
    
    # 3. صياغة التحليلات، الأسباب، والحلول الفورية بداخل تقرير الـ PDF
    story.append(Paragraph("<b>2. Autonomous Root-Cause & Actionable Diagnostics</b>", header_style))
    
    has_issues = False
    if oxygen < 5.5:
        has_issues = True
        story.append(Paragraph(f"🚨 <b>[CRITICAL CRASH] Low Dissolved Oxygen:</b> {oxygen:.2f} mg/L", alert_style))
        story.append(Paragraph("• <u>The Cause:</u> Aerator failure, organic overload, or sudden fish bioload explosion.", body_style))
        story.append(Paragraph("• <u>Immediate Action Required:</u> Override main relays, activate the auxiliary aeration backup grid (Aerator 2) at 100% capacity.", body_style))
        story.append(Spacer(1, 5))
        
    if water_temp > 28.5:
        has_issues = True
        story.append(Paragraph(f"🚨 <b>[THERMAL SHOCK] High Water Temperature:</b> {water_temp:.2f} °C", alert_style))
        story.append(Paragraph("• <u>The Cause:</u> Direct solar radiation load or cooling fan failure.", body_style))
        story.append(Paragraph("• <u>Immediate Action Required:</u> Force-start the inline Chiller loop and activate the biological shade actuators.", body_style))
        story.append(Spacer(1, 5))

    if ammonia > 0.3:
        has_issues = True
        story.append(Paragraph(f"🚨 <b>[BIOCHEMICAL TOXICITY] Elevated Ammonia Load:</b> {ammonia:.2f} ppm", alert_style))
        story.append(Paragraph("• <u>The Cause:</u> Over-feeding of feedstock, unconsumed feed decomposition, or biofilter bacteria breakdown.", body_style))
        story.append(Paragraph("• <u>Immediate Action Required:</u> Execute an automated 20% water flush, restrict feeding calculator access for 12 cycles, and verify biofilter mesh status.", body_style))
        story.append(Spacer(1, 5))
        
    if water_level < 40.0:
        has_issues = True
        story.append(Paragraph(f"🚨 <b>[HYDRO-SHORTAGE] Low Water Tank Level:</b> {water_level:.2f} %", alert_style))
        story.append(Paragraph("• <u>The Cause:</u> Physical pipe rupture, evaporation rate leakage, or pump backflow.", body_style))
        story.append(Paragraph("• <u>Immediate Action Required:</u> Trigger the electronic Solenoid valve to initiate auto-refill sequence.", body_style))
        story.append(Spacer(1, 5))

    if not has_issues:
        story.append(Paragraph("🟢 <b>All Core Matrices Stable:</b> No biological deviations detected across the ecosystem.", body_style))
        story.append(Paragraph("• <u>Ecosystem Report Status:</u> The Nitrogen cycle is fully balanced. Plants absorbing nitrate ions at standard metabolic rates.", body_style))
        
    story.append(Spacer(1, 10))
    story.append(Paragraph("<b>3. Fish Biomass Configuration Status</b>", header_style))
    story.append(Paragraph(f"• Total Fish Count: <b>{fish_data['fish_count']} Pcs</b> | Net Calculated Biomass: <b>{total_biomass_kg:.2f} kg</b>", body_style))
    story.append(Paragraph(f"• Global Ecosystem Health Rating: <b>{score}/100</b> | Feed Efficiency Score: <b>{feeding_score}/100</b>", body_style))
    
    doc.build(story)
    return filename


# =========================================================================
# 📊 شريط المؤشرات الإحصائي العلوي   
# =========================================================================
st.markdown("<h2 style='text-align: center; color: #ffffff; font-weight: 800; margin-bottom: 20px;'>AQUA MIND AI </h2>", unsafe_allow_html=True)

# استخراج أعلى وأوطى قيم تاريخية حقيقية لضخها في شريط المؤشرات العلوي
max_temp_recorded = df_stats["water_temp"].max() if not df_stats.empty else water_temp
min_oxygen_recorded = df_stats["oxygen"].min() if not df_stats.empty else oxygen
latest_hub_region = "Cairo Cluster"
top_segment_tag = "Premium"

st.markdown(f"""
<div class="bi-top-ribbon-container">
    <div class="bi-ribbon-card"><div class="bi-ribbon-title">Top Region</div><div class="bi-ribbon-value">{latest_hub_region}</div></div>
    <div class="bi-ribbon-card"><div class="bi-ribbon-title">Top Segment</div><div class="bi-ribbon-value">{top_segment_tag}</div></div>
    <div class="bi-ribbon-card"><div class="bi-ribbon-title">Max Temperature</div><div class="bi-ribbon-value">{max_temp_recorded:.1f}°C</div></div>
    <div class="bi-ribbon-card"><div class="bi-ribbon-title">Min Dissolved O₂</div><div class="bi-ribbon-value">{min_oxygen_recorded:.1f} mg/L</div></div>
    <div class="bi-ribbon-card"><div class="bi-ribbon-title">System Health Mode</div><div class="bi-ribbon-value" style="color: {'#ef4444' if 'CRITICAL' in mode else '#22c55e'}">{mode}</div></div>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (لوحة التحكم الجانبية ) ---
with st.sidebar:
    st.markdown("<h3 style='color: #ffffff; font-weight: 700;'>🎛️ Diagnostic Panel</h3>", unsafe_allow_html=True)
    st.metric("Ecosystem Health", f"{score}/100")
    st.markdown("---")
    st.info(" Real-time Business Intelligence Pipeline active. Twin sync complete.")

# --- MAIN ALERTS (التنبيهات العلوية) ---
if feeding_score >= 85 and score >= 85:
    st.success(f" المنظومة البيئية مستقرة تماماً ومثالية! سكور التغذية الحالية: {feeding_score}% وصحة النظام الإجمالية ممتازة.")
elif feeding_score < 70 or "CRITICAL" in mode:
    st.error(f" انتباه: يوجد خلل تشغيلي حرج! سكور إدارة التغذية انخفض إلى {feeding_score}%. يرجى مراجعة كميات العلف فوراً.")
else:
    st.warning(" النظام في وضع التحذير المعتدل. يرجى مراقبة جودة الفلترة الحيوية ومستويات النيترات.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Telemetry Dashboard & BI Data",
    "🤖 Predictive Machine Learning AI",
    "🐟 Biomass Feed Optimization",
    "📄 Automated Production Reports"
])

# ==========================================
# --- TAB 1: TELEMETRY DASHBOARD & BI DATA ---
# ==========================================
with tab1:
    col_dash1, col_dash2 = st.columns([1.1, 0.9]) #    توزيع الأعمدة بنسبة 55% و 45% لعرض البيانات و الؤشرات 
    
    with col_dash1:
        st.markdown("<h4 style='color: #ffffff; font-weight: 700;'> Active Environmental Telemetry </h4>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("🌡️ Water Temp", f"{water_temp} °C")
        c2.metric("🧪 pH Level", ph)
        c3.metric("🫧 Dissolved Oxygen", f"{oxygen} mg/L")
        
        c4, c5, c6 = st.columns(3)
        c4.metric("💧 Air Humidity", f"{humidity} %")
        c5.metric("🌬️ Air Temp", f"{air_temp} °C")
        c6.metric("🚰 Water Level", f"{water_level} %")
        
        st.divider()
        st.markdown("<h4 style='color: #ffffff; font-weight: 700;'>📈 Micro-Telemetry Historical Run Profile (Last 30 Cycles)</h4>", unsafe_allow_html=True)
        if not df_stats.empty:
            df_history = df_stats.tail(30).set_index("time") if "time" in df_stats.columns else df_stats.tail(30)
            st.line_chart(df_history[["water_temp", "oxygen", "ph"]])

    with col_dash2:
        st.markdown("<h4 style='color: #ffffff; font-weight: 700;'>📋 Chemical Composition & Target Reference Matrix</h4>", unsafe_allow_html=True)
        # مصفوفة مقارنة وتحليل الداتا الكيميائية      
        st.markdown(f"""
        <table class="styled-table">
            <thead>
                <tr><th>Chemical Parameter</th><th>Current Simulation</th><th>Target Reference</th></tr>
            </thead>
            <tbody>
                <tr><td>Ammonia (NH3) Load</td><td>{ammonia} ppm</td><td>&lt; 0.25 ppm (Safe)</td></tr>
                <tr><td>Nitrite (NO2) Load</td><td>{nitrite} ppm</td><td>&lt; 0.05 ppm (Optimal)</td></tr>
                <tr><td>Nitrate (NO3) Level</td><td>{nitrate} ppm</td><td>10 - 40 ppm (Botanical Nutrient)</td></tr>
                <tr><td>Hydro-Pump Flow Rate</td><td>{flow_rate} L/min</td><td>&gt; 1.0 L/min (Active)</td></tr>
            </tbody>
        </table>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><h4 style='color: #ffffff; font-weight: 700;'>🧫 Nutrient Load Distribution Analysis</h4>", unsafe_allow_html=True)
        # رسم توزيع العناصر والمغذيات       
        nutrient_pie_data = pd.DataFrame({
            "Nutrient Core Element": ["Nitrate Fertilizer Base", "Ammonia Bio Load", "Added Supplement Factor"],
            "Volumetric Ratio": [nitrate, ammonia * 10, 6.5]
        })
        st.bar_chart(nutrient_pie_data.set_index("Nutrient Core Element")) # تمثيل بياني عمودي    
        st.dataframe(nutrient_pie_data, use_container_width=True) # عرض الجدول البياني مع ملء العرض الكامل للعمود   

# ==========================================
# --- TAB 2: PREDICTIVE MACHINE LEARNING AI ---
# ==========================================
with tab2:
    st.markdown("####  Plant Health Analysis & Fish Vitality Prognostics")
    if plant_model is not None:
        try:
            plant_pred = plant_model.predict(pd.DataFrame([[ph, nitrate, humidity, air_temp]], columns=["ph", "nitrate", "humidity", "air_temp"]))
            st.success(f" ML Model Predictive Output Vector: **{plant_pred}**")
        except: 
            pass
    else:
        st.error(" Plant Machine Learning Model file is offline. Model artifact missing.")

    st.divider()
    col_an1, col_an2 = st.columns(2)
    with col_an1:
        bio_ratio = round((fish_data["fish_count"] / nitrate) if nitrate > 0 else 0, 2)
        bio_ratio = round((fish_data["fish_count"] / nitrate) if nitrate > 0 else 0, 2)
        if bio_ratio > 15: 
            st.error(" كثافة سمكية زائدة! الفلتر الحيوي يواجه عجزاً في الفلترة.")
        else: 
            st.success("  التوازن البيئي  لدورة النيتروجين.جيد جداً بالنسبة لعدد الأسماك الحالي.")


    with col_an2:
        if fish_model is not None:
            try:
                fish_pred = fish_model.predict(pd.DataFrame([[water_temp, ph, oxygen]], columns=['water_temp', 'ph', 'oxygen']))
            except: 
                pass
        else:
            st.error(" Fish Machine Learning Model file is offline. Model artifact missing.")
            
    
# ==========================================
# --- TAB 3: BIOMASS FEED OPTIMIZATION ENGINE ---
# ==========================================
with tab3:
    st.markdown("#### Biomass Allocation & Food Budgeting Configuration Panel")
    col_input1, col_input2, col_input3 = st.columns(3)
    col_input1, col_input2, col_input3 = st.columns(3)
    with col_input1: 
        fish_count_input = st.number_input(" Active Stock Count:", min_value=1, value=int(fish_data.get("fish_count", 100)), step=10)
    with col_input2: 
        avg_weight_input = st.number_input(" Mean Weight per Unit (g):", min_value=1.0, value=float(fish_data.get("avg_weight", 200.0)), step=5.0)

        feeding_rate_input = st.number_input(" Target Feed Ratio (% Body Weight):", min_value=0.5, max_value=10.0, value=float(fish_data.get("feeding_rate", 2.0)), step=0.5)


    # store the current feeding rate input in session state (fallback to feeding_rate_input)
    st.session_state["actual_feed_input"] = feeding_rate_input

    calculated_biomass_kg = (fish_count_input * avg_weight_input) / 1000.0
    st.metric("Net Biomass Metric", f"{calculated_biomass_kg:.2f} kg")
    
    if st.button("💾 Apply Configuration to Digital Twin"):
        save_fish_settings(fish_count_input, avg_weight_input, feeding_rate_input)


# ==========================================
# --- TAB 4: AUTOMATED PRODUCTION REPORTS ---
# ==========================================
with tab4:
    
    if REPORTLAB_AVAILABLE:
        if st.button("Execute Automated Document Compilation Pipeline"):
            pdf_file = build_pdf_report()
            with open(pdf_file, "rb") as f:
                st.download_button(label="📥 Secure Production-Ready PDF Report Artifact", data=f, file_name=pdf_file, mime="application/pdf")
    else:
        st.error(" ReportLab library is not installed. PDF generation functionality is unavailable.")

