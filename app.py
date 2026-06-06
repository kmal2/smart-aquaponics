import sqlite3
import joblib
import os
import streamlit as st
import requests
import pandas as pd
import datetime
import numpy as np
from streamlit_autorefresh import st_autorefresh
from db import insert_data

# =========================
# NOTIFICATIONS (NEW)
# =========================
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

TWILIO_SID = os.getenv("TWILIO_SID", "")
TWILIO_AUTH = os.getenv("TWILIO_AUTH", "")
WHATSAPP_TO = os.getenv("WHATSAPP_TO", "")

def send_telegram(msg):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
                timeout=3
            )
        except:
            pass

def send_whatsapp(msg):
    if not TWILIO_SID:
        return
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_AUTH)
        client.messages.create(
            body=msg,
            from_="whatsapp:+14155238886",
            to=WHATSAPP_TO
        )
    except:
        pass


# =========================
# CONFIG
# =========================
BLYNK_AUTH = os.getenv("BLYNK_AUTH", "YOUR_TOKEN")

st.set_page_config(page_title="Aquaponics Final Capstone", layout="wide")

st.markdown("""
<style>
.main {
    background: radial-gradient(circle at top, #111827, #0b0f19);
    color: white;
}

div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.08);
    padding: 14px;
    border-radius: 16px;
}

h1, h2, h3 {
    color: #ffffff;
    font-weight: 700;
}

.stButton button {
    border-radius: 10px;
    background: linear-gradient(90deg, #2563eb, #1d4ed8);
    color: white;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

st.title("🌱 Aquaponics AI System")
st.caption("AI + IoT + Analytics + Control Panel")

st_autorefresh(interval=10000, key="refresh")

# =========================
# MODELS (FIXED SAFE LOAD)
# =========================
try:
    plant_model = joblib.load("plant_health_model.pkl")
    fish_model = joblib.load("fish_health_model.pkl")
    models_loaded = True
except:
    models_loaded = False

# =========================
# FORECAST MODEL (FIXED - ONLY ONE LOAD)
# =========================
try:
    forecast_model = joblib.load("forecast_model.pkl")
except:
    forecast_model = None


# =========================
# BLYNK
# =========================
def get_blynk(pin):
    try:
        r = requests.get(f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&{pin}", timeout=3)
        return float(r.text)
    except:
        return 0.0

def send_to_blynk(pin, value):
    try:
        requests.get(f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&{pin}={value}", timeout=3)
    except:
        pass


# =========================
# LIVE DATA
# =========================
water_temp = get_blynk("v0")
ph = get_blynk("v1")
oxygen = get_blynk("v2")
humidity = get_blynk("v3")
air_temp = get_blynk("v4")
water_level = get_blynk("v5")
ammonia = get_blynk("v6")
nitrite = get_blynk("v7")
nitrate = get_blynk("v8")
flow_rate = get_blynk("v9")
pump_failure = False

if flow_rate < 0.5:
    pump_failure = True

water_leak = False

if water_level < 20:
    water_leak = True
# =========================
# SYSTEM MODE (FIXED SAFE POSITION)
# =========================
def get_system_mode():

    if (
        oxygen < 5
        or water_temp > 32
        or ammonia > 0.5
        or nitrite > 1
        or water_level < 20
    ):
        return "🔴 CRITICAL"

    elif ph < 6 or ph > 8:
        return "🟡 WARNING"

    return "🟢 OPTIMAL"

system_mode = get_system_mode()


# =========================
# AI MODELS
# =========================
plant_status = "Unknown"
fish_status = "Unknown"

if models_loaded:
    plant_input = pd.DataFrame([{
        "water_temp": water_temp,
        "ph": ph,
        "oxygen": oxygen,
        "humidity": humidity
    }])

    fish_input = pd.DataFrame([{
        "water_temp": water_temp,
        "ph": ph,
        "oxygen": oxygen
    }])

    plant_status = plant_model.predict(plant_input)[0]
    fish_status = fish_model.predict(fish_input)[0]


# =========================
# ENGINE (UNCHANGED LOGIC)
# =========================
score = 100
reasons = []

if oxygen < 5:
    score -= 30
    reasons.append("Low oxygen level detected")

if water_temp > 30:
    score -= 20
    reasons.append("High temperature stress")

if ph < 6 or ph > 8:
    score -= 20
    reasons.append("pH imbalance")
if ammonia > 0.5:
    score -= 25
    reasons.append("High ammonia level")

if nitrite > 1:
    score -= 20
    reasons.append("High nitrite level")

if flow_rate < 1:
    score -= 15
    reasons.append("Low water circulation")
if "healthy" not in str(plant_status).lower():
    score -= 10
    reasons.append("Plant stress detected")

if "healthy" not in str(fish_status).lower():
    score -= 15
    reasons.append("Fish stress detected")
if water_level < 20:
    score -= 20
    reasons.append("Critical water level drop")
if nitrate > 150:
    score -= 10
    reasons.append("High nitrate accumulation")

def severity(score, reasons):
    if score >= 90:
        return "🟢 PERFECT"
    elif score >= 70:
        return "🟡 GOOD"
    elif score >= 50:
        return "🟠 WARNING"
    return "🔴 CRITICAL"


score = max(score, 0)
stability = min(100, score)
health_state = severity(score, reasons)

# =========================
# ALERT ENGINE (UNCHANGED)
# =========================
def trigger_notifications():
    if not reasons:
        return

    msg = f"""
🌱 AQUAPONICS PRO ALERT

📊 Score: {score}/100
⚡ Stability: {stability}/100
🚨 Status: {health_state}

Issues:
- """ + "\n- ".join(reasons)

    if "last_alert" not in st.session_state:
        st.session_state.last_alert = ""

    now_key = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if st.session_state.last_alert != now_key:
        send_telegram(msg)
        send_whatsapp(msg)
        st.session_state.last_alert = now_key

trigger_notifications()


# =========================
# SAVE DB (UNCHANGED)
# =========================
now = datetime.datetime.now()

if "last_save" not in st.session_state:
    st.session_state.last_save = ""

if st.session_state.last_save != now.strftime("%Y-%m-%d %H:%M"):
    insert_data((
    now.strftime("%Y-%m-%d %H:%M:%S"),
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
))
    st.session_state.last_save = now.strftime("%Y-%m-%d %H:%M")


# =========================
# HISTORY
# =========================
if "history" not in st.session_state:
    st.session_state.history = []

st.session_state.history.append({
    "time": now.strftime("%H:%M:%S"),
    "water_temp": water_temp,
    "ph": ph,
    "oxygen": oxygen,
    "humidity": humidity,
    "water_level": water_level,
    "ammonia": ammonia,
    "nitrite": nitrite,
    "nitrate": nitrate,
    "flow_rate": flow_rate,
    "score": score,
    "stability": stability
})

# Keep only last 500 records
if len(st.session_state.history) > 500:
    st.session_state.history = st.session_state.history[-500:]
df = pd.DataFrame(st.session_state.history[-60:])
oxygen_trend = "Stable"

if len(df) > 10:
    if df["oxygen"].iloc[-1] > df["oxygen"].iloc[-10]:
        oxygen_trend = "Increasing"

    elif df["oxygen"].iloc[-1] < df["oxygen"].iloc[-10]:
        oxygen_trend = "Decreasing"

# =========================
# FEATURE BUILDER (FIXED SAFE VERSION)
# =========================
def build_lag_features(df):
    data = {}

    for i in range(1, 6):
        data[f"oxygen_lag_{i}"] = df["oxygen"].iloc[-i] if len(df) > i else oxygen
        data[f"temp_lag_{i}"] = df["water_temp"].iloc[-i] if len(df) > i else water_temp
        data[f"ph_lag_{i}"] = df["ph"].iloc[-i] if len(df) > i else ph

    return pd.DataFrame([data])


# =========================
# AI PREDICTION ENGINE
# =========================
predicted_oxygen = None

if forecast_model is not None and len(df) >= 5:
    input_data = build_lag_features(df)
    predicted_oxygen = forecast_model.predict(input_data)[0]

# =========================
# CONTROL PANEL
# =========================
st.subheader("🎛 Control Panel")

colA, colB, colC = st.columns(3)

with colA:
    if st.button("💧 Pump ON"):
        send_to_blynk("v10", 1)
    if st.button("💧 Pump OFF"):
        send_to_blynk("v10", 0)

with colB:
    if st.button("💨 Oxygen ON"):
        send_to_blynk("v11", 1)
    if st.button("💨 Oxygen OFF"):
        send_to_blynk("v11", 0)

with colC:
    if st.button("💡 Light ON"):
        send_to_blynk("v12", 1)
    if st.button("💡 Light OFF"):
        send_to_blynk("v12", 0)

st.subheader("🤖 Auto Control")

auto_mode = st.toggle("Enable Smart Automation")
if auto_mode:

    if oxygen < 5:
        send_to_blynk("v11", 1)

    if water_temp > 30:
        send_to_blynk("v12", 0)

    if flow_rate < 1:
        send_to_blynk("v10", 1)
# =========================
# SYSTEM OVERVIEW
# =========================
st.subheader("📊 System Overview")

c1, c2, c3 = st.columns(3)
c1.metric("💚 Health Score", f"{score}/100", health_state)
c2.metric("⚡ Stability", f"{stability}/100", health_state)
c3.metric("🚨 Status", system_mode)
aquaponics_index = 100

if oxygen < 5:
    aquaponics_index -= 25

if ph < 6.5 or ph > 7.5:
    aquaponics_index -= 20

if ammonia > 0.5:
    aquaponics_index -= 25

if nitrite > 1:
    aquaponics_index -= 15

if water_temp < 20 or water_temp > 30:
    aquaponics_index -= 15

aquaponics_index = max(0, aquaponics_index)
aquaponics_index = max(
    0,
    min(100, aquaponics_index)
)

st.metric(
    "🌱 Aquaponics Health Index",
    f"{aquaponics_index:.1f}/100"
)
st.metric(
    "🐟 Fish Survival Probability",
    f"{max(0, score):.0f}%"
)
# =========================
# PREDICTION UI (FIXED SECTION)
# =========================
st.subheader("🔮 AI Prediction Engine")

if predicted_oxygen is not None:
    st.metric(
        "Predicted Oxygen (Next Step)",
        f"{predicted_oxygen:.2f} mg/L"
    )
else:
    st.info("Not enough data for prediction yet (need ≥ 5 readings)")


# =========================
# SMART RISK (NEW UPGRADE - ADDED ONLY)
# =========================
st.subheader("🧠 Smart Risk Forecast")

future_risk = score

if predicted_oxygen is not None:
    if predicted_oxygen < 5:
        future_risk -= 20

future_risk = max(0, future_risk)
explanation = []

if predicted_oxygen is not None:
    if predicted_oxygen < 5:
        explanation.append(
            "Oxygen expected to drop below safe level."
        )

if ammonia > 0.5:
    explanation.append(
        "Ammonia accumulation detected."
    )

if flow_rate < 1:
    explanation.append(
        "Water circulation is weak."
    )
st.metric("Future Risk Score", f"{future_risk:.2f}")
if explanation:
    st.warning(" | ".join(explanation))
else:
    st.success("AI sees no future risks.")
# =========================
# Explainable AI
# =========================
st.subheader("🧠 Explainable AI")

ai_comment = []

if oxygen < 5:
    ai_comment.append(
        "Oxygen concentration is below safe fish threshold."
    )

if ammonia > 0.5:
    ai_comment.append(
        "Ammonia accumulation may stress fish."
    )

if flow_rate < 1:
    ai_comment.append(
        "Poor water circulation detected."
    )

if predicted_oxygen is not None:
    if predicted_oxygen < oxygen:
        ai_comment.append(
            "Forecast model predicts oxygen decline."
        )

for comment in ai_comment:
    st.info(comment)
# =========================
# AI Recommendations
# =========================
st.subheader("🤖 AI Recommendations")

if oxygen < 5:
    st.warning(
        "Turn ON aerator immediately."
    )

if ammonia > 0.5:
    st.warning(
        "Reduce feeding and perform water exchange."
    )

if ph < 6:
    st.warning(
        "Increase pH gradually."
    )

if ph > 8:
    st.warning(
        "Decrease pH gradually."
    )

if not reasons:
    st.success(
        "System operating within optimal range."
    )
# =========================
#Sensor Status Monitor
# =========================
st.subheader("🔌 Sensor Status")

sensor_status = {
    "Water Temp": water_temp,
    "pH": ph,
    "Oxygen": oxygen,
    "Water Level": water_level,
    "Ammonia": ammonia,
    "Nitrite": nitrite,
    "Nitrate": nitrate
}

for name, value in sensor_status.items():

    if value <= 0 and name in ["Water Temp", "pH", "Oxygen"]:
        st.error(f"{name}: Offline")
    else:
        st.success(f"{name}: Online")
# =========================
# SENSOR DISPLAY
# =========================
st.subheader("📡 Live Sensors")
st.subheader("🧪 Water Quality")

q1, q2, q3, q4 = st.columns(4)

q1.metric("NH3 Ammonia", ammonia)
q2.metric("Nitrite", nitrite)
q3.metric("Nitrate", nitrate)
q4.metric("Flow Rate", flow_rate)
col1, col2, col3 = st.columns(3)
col1.metric("🌡 Temp", water_temp)
col2.metric("🧪 pH", ph)
col3.metric("🫧 Oxygen", oxygen)

col4, col5, col6 = st.columns(3)
col4.metric("💧 Humidity", humidity)
col5.metric("🌬 Air Temp", air_temp)
col6.metric("🚰 Water Level", water_level)


# =========================
# AI STATUS
# =========================
st.subheader("🧠 AI System Status")

col1, col2 = st.columns(2)
col1.metric("🌱 Crop Status", plant_status)
col2.metric("🐟 Aquatic Status", fish_status)


# =========================
# ALERTS
# =========================
st.subheader("🚨 Alerts")

if reasons:
    for r in reasons:
        st.error(r)
else:
    st.success("System Stable")

if pump_failure:
    st.error("🚨 Pump Failure Suspected")
if water_leak:
    st.error("🚨 Possible Water Leak")
# =========================
# TREND
# =========================
st.subheader("📈 Trends")

st.line_chart(df[["water_temp", "ph", "oxygen"]])
if all(col in df.columns for col in ["ammonia", "nitrite", "nitrate"]):

    st.subheader("🧪 Water Chemistry Trends")

    st.line_chart(
        df[
            [
                "ammonia",
                "nitrite",
                "nitrate"
            ]
        ]
    )
st.metric(
    "Oxygen Trend",
    oxygen_trend
)
if "score" in df.columns:

    st.subheader("💚 System Health Trend")

    st.line_chart(df[["score"]])
# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Final Capstone System | AI + IoT + Alerts + Forecast + Control")