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

st.title("🌱 Aquaponics Final Capstone System")
st.caption("AI + IoT + Analytics + Control Panel")

st_autorefresh(interval=3000, key="refresh")


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


# =========================
# SYSTEM MODE (FIXED SAFE POSITION)
# =========================
def get_system_mode():
    if oxygen < 5 or water_temp > 32:
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

if "healthy" not in str(plant_status).lower():
    score -= 10
    reasons.append("Plant stress detected")

if "healthy" not in str(fish_status).lower():
    score -= 15
    reasons.append("Fish stress detected")

score = max(score, 0)
stability = 100 - abs(50 - score)


def severity(score, reasons):
    if score > 80 and not reasons:
        return "🟢 PERFECT"
    elif score > 70:
        return "🟡 GOOD"
    elif score > 50:
        return "🟠 WARNING"
    return "🔴 CRITICAL"

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
    insert_data((now.strftime("%Y-%m-%d %H:%M:%S"),
                 water_temp, ph, oxygen, humidity, air_temp, water_level))
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
    "humidity": humidity
})

df = pd.DataFrame(st.session_state.history[-60:])


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


# =========================
# SYSTEM OVERVIEW
# =========================
st.subheader("📊 System Overview")

c1, c2, c3 = st.columns(3)
c1.metric("💚 Health Score", f"{score}/100", health_state)
c2.metric("⚡ Stability", f"{stability}/100", health_state)
c3.metric("🚨 Status", system_mode)


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

future_risk = score - (0.3 if predicted_oxygen and predicted_oxygen < 5 else 0)

st.metric("Future Risk Score", f"{future_risk:.2f}")


# =========================
# SENSOR DISPLAY
# =========================
st.subheader("📡 Live Sensors")

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


# =========================
# TREND
# =========================
st.subheader("📈 Trends")

st.line_chart(df[["water_temp", "ph", "oxygen"]])


# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Final Capstone System | AI + IoT + Alerts + Forecast + Control")