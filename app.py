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
.main {background-color:#0e1117;color:white;}
.stMetric {background-color:#1c1f26;padding:10px;border-radius:10px;}
.block-container {padding-top:1.2rem;}
</style>
""", unsafe_allow_html=True)

st.title("🌱 Aquaponics Final Capstone System")
st.caption("AI + IoT + Analytics + Control Panel")

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=3000, key="refresh")

# =========================
# MODELS
# =========================
try:
    plant_model = joblib.load("plant_health_model.pkl")
    fish_model = joblib.load("fish_health_model.pkl")
    models_loaded = True
except:
    models_loaded = False

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
# AI
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
# ENGINE (PRO)
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

def level(x):
    if x > 80:
        return "🟢 Stable"
    elif x > 50:
        return "🟡 Warning"
    return "🔴 Critical"

# =========================
# PRO ALERT SEVERITY
# =========================
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
# AI SUMMARY
# =========================
def ai_summary():
    if score > 80:
        return "System is operating optimally."
    elif score > 60:
        return "System is stable but needs monitoring."
    elif score > 40:
        return "System stress detected."
    else:
        return "Critical risk detected!"

summary_text = ai_summary()

# =========================
# ALERT ENGINE
# =========================
def trigger_notifications():
    if not reasons:
        return

    msg = f"""
🌱 AQUAPONICS PRO ALERT SYSTEM

📊 Health Score: {score}/100
⚡ Stability: {stability}/100
🚨 Status: {health_state}

📌 Issues:
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
# SAVE DB
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
# DASHBOARD
# =========================
st.subheader("📊 System Overview")

c1,c2,c3 = st.columns(3)
c1.metric("💚 Health Score", f"{score}/100", health_state)
c2.metric("⚡ Stability", f"{stability}/100", health_state)
c3.metric("🚨 Status", health_state)

# =========================
# SENSORS
# =========================
st.subheader("📡 Live Sensors")

col1,col2,col3 = st.columns(3)
col1.metric("🌡 Temp", f"{water_temp}°C")
col2.metric("🧪 pH", ph)
col3.metric("🫧 Oxygen", oxygen)

col4,col5,col6 = st.columns(3)
col4.metric("💧 Humidity", humidity)
col5.metric("🌬 Air Temp", air_temp)
col6.metric("🚰 Water Level", water_level)

st.caption("🔄 Live IoT data updating every 3 seconds")

# =========================
# AI SECTION
# =========================
st.subheader("🧠 AI System Status")

col1,col2 = st.columns(2)
col1.metric("🌱 Crop Status", plant_status)
col2.metric("🐟 Aquatic Status", fish_status)

# =========================
# DIAGNOSTIC
# =========================
st.subheader("📋 AI Diagnostic Report")

if reasons:
    for r in reasons:
        st.warning("⚠️ " + r)
else:
    st.success("All systems optimal")

st.success("🧠 AI Insight: " + summary_text)

# =========================
# TREND
# =========================
st.subheader("📈 Trend Analysis")

st.line_chart(df[["water_temp","ph","oxygen"]])

st.write("📊 Avg Oxygen:", round(df["oxygen"].mean(),2))
st.write("📊 Avg Temp:", round(df["water_temp"].mean(),2))

# =========================
# SUMMARY
# =========================
st.subheader("📄 System Summary")

st.info(f"""
- Health Score: {score}/100  
- Stability: {stability}/100  
- Oxygen: {oxygen}  
- Plant Status: {plant_status}  
- Fish Status: {fish_status}  
- Alerts: {len(reasons)}  
- System State: {health_state}
""")

# =========================
# ALERTS
# =========================
st.subheader("🚨 Alerts")

if reasons:
    for r in reasons:
        st.error(r)
else:
    st.success("No critical alerts detected")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Final Capstone System | PRO VERSION (AI + IoT + Notifications + Analytics)")