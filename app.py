import os
import time
import json
import joblib
import requests
import datetime
import pandas as pd
import streamlit as st
try:
    from streamlit_autorefresh import st_autorefresh
except ImportError:
    def st_autorefresh(interval=0, limit=None, key=None):
        return None
from db import insert_data
import sqlite3
from report import generate_pdf

try:
    plant_model = joblib.load("plant_health_model.pkl")
except:
    plant_model = None

try:
    fish_model = joblib.load("fish_health_model.pkl")
except:
    fish_model = None

try:
    oxygen_model = joblib.load("oxygen_forecast.pkl")
except:
    oxygen_model = None


def get_history(limit=50):
    conn = sqlite3.connect("aquaponics.db")

    query = """
    SELECT *
    FROM sensor_data
    ORDER BY id DESC
    LIMIT ?
    """

    df = pd.read_sql(query, conn, params=(limit,))
    conn.close()

    return df.iloc[::-1]


# =========================
# CONFIG
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8976549075:AAEXwqK80xq4rxxeYUA8bNRYmSQ6_GUdNJ8")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "8976549075")
BLYNK_AUTH = os.getenv("BLYNK_AUTH", "05GthB1qrQcqSaToJwwYyruodxK-_WdV")

# =========================
# PAGE CONFIG (ENTERPRISE UI)
# =========================
st.set_page_config(
    page_title="Aquaponics IoT Control Center",
    layout="wide",
    initial_sidebar_state="expanded"
)
# =========================
# BLYNK FUNCTIONS
# =========================

def blynk_send(pin, value):
    try:
        url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&{pin}={value}"
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print("Blynk error:", e)
        return False
# =========================
# PROFESSIONAL DARK UI
# =========================
st.markdown("""
<style>
.main {
    background: #0b1220;
    color: #ffffff;
}

.block-container {
    padding-top: 2rem;
    padding-left: 2rem;
    padding-right: 2rem;
}

div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 14px;
    border-radius: 14px;
}

.stButton button {
    background: linear-gradient(90deg,#2563eb,#1d4ed8);
    color: white;
    border-radius: 10px;
    font-weight: bold;
}

h1,h2,h3 {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=5000)
st.sidebar.info("🔄 System is running in Live Mode (5s refresh)")
# =========================
# DATA SOURCE
# =========================
import shared_data

def get_data():
    return shared_data.DATA

data = get_data() or {}

def safe(v):
    return 0.0 if v is None else v
# =========================
# TELEGRAM FIX
# =========================
def send_telegram(msg):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg
        }, timeout=5)
    except:
        pass

send_telegram("TEST ALERT")
# =========================
# BLYNK FIX
# =========================
def send_once(key, value):
    storage_key = f"last_{key}"

    if storage_key not in st.session_state:
        st.session_state[storage_key] = None

    if st.session_state[storage_key] == value:
        return False

    st.session_state[storage_key] = value
    return True
def blynk_get(pin):
    try:
        url = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&{pin}"
        r = requests.get(url, timeout=5)

        print(f"Blynk {pin} raw:", r.text)

        value = r.text.strip()

        if value in ["", "null", "None", "[]"]:
            return None

        return float(value)

    except Exception as e:
        print("Blynk GET error:", e)
        return None

# =========================
# SENSOR MAPPING (FIXED)
# =========================

def safe_blynk(pin):
    val = blynk_get(pin)
    if val is None:
        print(f"⚠️ Missing Blynk data: {pin}")
        return 0.0
    return val


sensors = {
    "water_temp": safe_blynk("v0"),
    "ph": safe_blynk("v1"),
    "oxygen": safe_blynk("v2"),
    "humidity": safe_blynk("v3"),
    "air_temp": safe_blynk("v4"),
    "water_level": safe_blynk("v5"),

    "ammonia": float(data.get("ammonia") or 0),
    "nitrite": float(data.get("nitrite") or 0),
    "nitrate": float(data.get("nitrate") or 0),
    "flow_rate": float(data.get("flow_rate") or 1)
}

# =========================
# SAFE CASTING LAYER (CRITICAL FIX)
# =========================

def safe_float(v, default=0.0):
    try:
        return float(v)
    except:
        return default


water_temp = safe_float(sensors.get("water_temp"))
ph = safe_float(sensors.get("ph"))
oxygen = safe_float(sensors.get("oxygen"))
humidity = safe_float(sensors.get("humidity"))
air_temp = safe_float(sensors.get("air_temp"))
water_level = safe_float(sensors.get("water_level"))

ammonia = safe_float(sensors.get("ammonia"))
nitrite = safe_float(sensors.get("nitrite"))
nitrate = safe_float(sensors.get("nitrate"))
flow_rate = safe_float(sensors.get("flow_rate"), 1.0)

# =========================
# DERIVED FLAGS
# =========================

pump_failure = flow_rate < 0.5
water_leak = water_level < 20
# =========================
# SYSTEM STATUS
# =========================
def system_mode(oxygen, water_temp, ph, water_level):
    if oxygen < 5 or water_temp > 32 or water_level < 20:
        return "🔴 CRITICAL"
    if ph < 6 or ph > 8:
        return "🟡 WARNING"
    return "🟢 OPTIMAL"
mode = system_mode(oxygen, water_temp, ph, water_level)

# =========================
# SCORE ENGINE
# =========================
score = 100
reasons = []

if oxygen < 5: reasons.append("Low oxygen"); score -= 25
if water_temp > 30: reasons.append("High temp"); score -= 15
if ph < 6 or ph > 8: reasons.append("pH issue"); score -= 15

score = max(score, 0)


# =========================
# SIDEBAR CONTROLS (FIXED ANTI-SPAM)
# =========================
with st.sidebar:
    st.title("⚙ IoT Control Center")

    st.metric("System Mode", mode)
    st.metric("Health Score", score)

# =========================
# SAFE TOGGLE ENGINE (GLOBAL)
# =========================

def push_if_changed(key, pin, value):
    if f"last_{key}" not in st.session_state:
        st.session_state[f"last_{key}"] = None

    if st.session_state[f"last_{key}"] != value:
        st.session_state[f"last_{key}"] = value
        blynk_send(pin, int(value))
# =========================
# SIDEBAR CONTROLS
# =========================

with st.sidebar:
    st.title("⚙ IoT Control Center")

    st.metric("System Mode", mode)
    st.metric("Health Score", score)

    pump_state = st.toggle("🚰 Water Pump", key="pump_ui")
    push_if_changed("pump", "v10", pump_state)

    oxygen_state = st.toggle("🫧 Oxygen Pump", key="oxygen_ui")
    push_if_changed("oxygen_pump", "v11", oxygen_state)

    light_state = st.toggle("💡 Grow Light", key="light_ui")
    push_if_changed("light", "v12", light_state)
# MAIN DASHBOARD
# =========================
st.title("🌱 Smart Aquaponics")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Dashboard",
    "🤖 AI Center",
    "🐟 Feeding",
    "📄 Reports"
])

# =========================
# TAB 1 FIXED (LAYOUT BUG FIXED)
# =========================
with tab1:

    c1,c2,c3 = st.columns(3)
    c1.metric("🌡 Temp", water_temp)
    c2.metric("🧪 pH", ph)
    c3.metric("🫧 Oxygen", oxygen)

    c4,c5,c6 = st.columns(3)
    c4.metric("💧 Humidity", humidity)
    c5.metric("🌬 Air Temp", air_temp)
    c6.metric("🚰 Water Level", water_level)

    st.divider()

    st.subheader("📊 Health Overview")
    st.metric("System Score", f"{score}/100", mode)

    st.subheader("🚨 Alerts")
    if reasons:
        for r in reasons:
            st.error(r)
    else:
        st.success("System Stable")

    if pump_failure:
        st.error("Pump Failure Detected")

    if water_leak:
        st.error("Water Leak Detected")

def run_plant_ai(model, water_temp, ph, oxygen, humidity):
    try:
        return model.predict(pd.DataFrame([{
            "water_temp": water_temp,
            "ph": ph,
            "oxygen": oxygen,
            "humidity": humidity
        }]))[0]
    except:
        return "N/A"
# =========================
# TAB 2 AI (CLEAN VERSION)
# =========================
with tab2:

    st.subheader("🤖 AI Analysis")

    plant_status = "N/A"
    fish_status = "N/A"
    st.subheader("📊 AI Confidence Layer")
    st.progress(int(score))
    # ================= PLANT AI =================
    if plant_model:
        try:
            plant_input = pd.DataFrame([{
                "water_temp": float(water_temp),
                "ph": float(ph),
                "oxygen": float(oxygen),
                "humidity": float(humidity)
            }])

            plant_status = plant_model.predict(plant_input)[0]

            st.metric("🌿 Plant Health", plant_status)

        except Exception as e:
            st.warning(f"Plant model error: {e}")

    # ================= FISH AI =================
    if fish_model:
        try:
            fish_input = pd.DataFrame([{
                "water_temp": float(water_temp),
                "ph": float(ph),
                "oxygen": float(oxygen)
            }])

            fish_status = fish_model.predict(fish_input)[0]

            st.metric("🐟 Fish Health", fish_status)

        except Exception as e:
            st.warning(f"Fish model error: {e}")
# =========================
# TAB 3 FEEDING
# =========================
with tab3:

    st.subheader("🐟 Feeding Calculator")

    fish_count = st.number_input("Fish Count", 100)
    avg_weight = st.number_input("Avg Weight", 0.5)
    feed_used = st.number_input("Feed Used", 2.0)

    biomass = fish_count * avg_weight

    if biomass > 0:
        feeding_rate = (feed_used / biomass) * 100
        st.metric("Feeding Rate %", round(feeding_rate, 2))


# =========================
# TAB 4 REPORTS
# =========================
with tab4:

    st.subheader("📄 Reports")

    if st.button("Generate PDF Report"):
        pdf_file = generate_pdf(sensors, "OK", "OK", reasons)
        st.success(f"Report Generated: {pdf_file}")


# =========================
# TREND FIX (SAFE CHECK)
# =========================
st.subheader("📈 Historical Trends")

history = get_history(50)

if history is not None and len(history) > 0:
    cols = ["water_temp", "ph", "oxygen", "flow_rate"]
    if all(c in history.columns for c in cols):
        st.line_chart(history[cols])


# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Enterprise IoT Dashboard | AI + Blynk + Alerts + Monitoring")