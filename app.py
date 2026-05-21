import streamlit as st
import requests
import pandas as pd
import datetime
import numpy as np

from streamlit_autorefresh import st_autorefresh
from db import insert_data

# =========================
# BLYNK CONFIG
# =========================
BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"

# =========================
# PAGE CONFIG
# =========================
st.set_page_config(page_title="Smart Aquaponics Dashboard", layout="wide")
st.title("🌱 Smart Aquaponics AI Dashboard")

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=3000, key="refresh")

# =========================
# SAFE BLYNK GET
# =========================
def get_blynk(pin):
    url = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&{pin}"
    try:
        r = requests.get(url, timeout=3)
        return float(r.text)
    except:
        return 0.0

# =========================
# SEND TO BLYNK
# =========================
def send_to_blynk(pin, value):
    url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&{pin}={value}"
    try:
        requests.get(url, timeout=3)
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
# SAVE TO DATABASE
# =========================
insert_data((
    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    water_temp,
    ph,
    oxygen,
    humidity,
    air_temp,
    water_level
))

# =========================
# SESSION HISTORY
# =========================
if "history" not in st.session_state:
    st.session_state.history = []

st.session_state.history.append({
    "time": datetime.datetime.now().strftime("%H:%M:%S"),
    "water_temp": water_temp,
    "ph": ph,
    "oxygen": oxygen,
    "humidity": humidity,
    "air_temp": air_temp,
    "water_level": water_level
})

st.session_state.history = st.session_state.history[-30:]

df = pd.DataFrame(st.session_state.history)

# =========================
# SENSOR DISPLAY
# =========================
st.subheader("📡 Live Sensors")

col1, col2, col3 = st.columns(3)

col1.metric("🌡 Water Temp", water_temp)
col2.metric("🧪 pH", ph)
col3.metric("🫧 Oxygen", oxygen)

col4, col5, col6 = st.columns(3)

col4.metric("💧 Humidity", humidity)
col5.metric("🌬 Air Temp", air_temp)
col6.metric("🚰 Water Level", water_level)

# =========================
# HEALTH SCORE
# =========================
st.divider()

score = 100

if oxygen < 5:
    score -= 30
if water_temp > 30:
    score -= 25
if ph < 6 or ph > 8:
    score -= 20

st.subheader("🤖 System Health")
st.metric("💚 Health Score", score)

if score > 80:
    st.success("🟢 System Healthy")
elif score > 50:
    st.warning("🟡 Warning State")
else:
    st.error("🔴 Critical State")

# =========================
# ALERTS
# =========================
st.divider()
st.subheader("🚨 Alerts")

alerts = []

if oxygen < 5:
    alerts.append("Low Oxygen")
if water_temp > 30:
    alerts.append("High Temperature")
if ph < 6 or ph > 8:
    alerts.append("pH Out of Range")
if humidity < 40:
    alerts.append("Low Humidity")

if len(alerts) == 0:
    st.success("System Stable")
else:
    for a in alerts:
        st.warning("⚠️ " + a)

# =========================
# MANUAL CONTROL
# =========================
st.divider()
st.subheader("🎮 Manual Control")

col1, col2 = st.columns(2)

with col1:
    st.write("Air Pump")

    if st.button("🔵 ON", key="pump_on"):
        send_to_blynk("v10", 1)

    if st.button("⚪ OFF", key="pump_off"):
        send_to_blynk("v10", 0)

with col2:
    st.write("Fan")

    if st.button("🟢 ON", key="fan_on"):
        send_to_blynk("v11", 1)

    if st.button("⚪ OFF", key="fan_off"):
        send_to_blynk("v11", 0)

# =========================
# CHARTS
# =========================
st.divider()
st.subheader("📊 Live Trends")

st.line_chart(df.set_index("time")[["water_temp", "ph", "oxygen"]])

# =========================
# =========================
# 🧠 AI ANOMALY DETECTION
# =========================
def detect_anomaly(values):
    if len(values) < 5:
        return False

    mean = np.mean(values)
    std = np.std(values)

    latest = values[-1]

    if std == 0:
        return False

    z_score = (latest - mean) / std

    return abs(z_score) > 2

st.divider()
st.subheader("🧠 AI Anomaly Detection")

oxygen_list = [x["oxygen"] for x in st.session_state.history]
temp_list = [x["water_temp"] for x in st.session_state.history]
ph_list = [x["ph"] for x in st.session_state.history]

oxygen_anomaly = detect_anomaly(oxygen_list)
temp_anomaly = detect_anomaly(temp_list)
ph_anomaly = detect_anomaly(ph_list)

if oxygen_anomaly:
    st.error("⚠️ Oxygen behavior is abnormal!")

if temp_anomaly:
    st.error("⚠️ Water temperature trend is unstable!")

if ph_anomaly:
    st.error("⚠️ pH values showing unusual pattern!")

if not oxygen_anomaly and not temp_anomaly and not ph_anomaly:
    st.success("🟢 System behavior is normal")

# =========================
# FOOTER
# =========================
st.caption("🔄 Smart IoT + AI + Blynk + Database System")