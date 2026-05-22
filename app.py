import streamlit as st
import requests
import pandas as pd
import datetime
import numpy as np
from streamlit_autorefresh import st_autorefresh
from db import insert_data

# =========================
# CONFIG
# =========================
BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"

st.set_page_config(page_title="Smart Aquaponics Dashboard", layout="wide")

st.markdown("""
<style>
.main {
    background-color: #0e1117;
    color: white;
}
.stMetric {
    background-color: #1c1f26;
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("# 🌱 Smart Aquaponics System")
st.markdown("### Real-Time IoT + AI Monitoring Dashboard")

# =========================
# AUTO REFRESH
# =========================
st_autorefresh(interval=3000, key="refresh")

# =========================
# FUNCTIONS
# =========================
def get_blynk(pin):
    url = f"https://blynk.cloud/external/api/get?token={BLYNK_AUTH}&{pin}"
    try:
        r = requests.get(url, timeout=3)
        return float(r.text)
    except:
        return 0.0


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
# HISTORY
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
# KPI CARDS
# =========================
st.markdown("## 📡 Live Sensors")

col1, col2, col3 = st.columns(3)
col1.metric("🌡 Water Temp", f"{water_temp} °C")
col2.metric("🧪 pH", ph)
col3.metric("🫧 Oxygen", oxygen)

col4, col5, col6 = st.columns(3)
col4.metric("💧 Humidity", humidity)
col5.metric("🌬 Air Temp", air_temp)
col6.metric("🚰 Water Level", water_level)

# =========================
# STATUS
# =========================
st.markdown("## 📊 System Status")

if oxygen < 5:
    st.error("🔴 Oxygen Critical")
elif oxygen < 6:
    st.warning("🟡 Oxygen Low")
else:
    st.success("🟢 Oxygen Normal")

# =========================
# HEALTH SCORE
# =========================
st.markdown("## 🤖 Health Score")

score = 100

if oxygen < 5:
    score -= 30
if water_temp > 30:
    score -= 25
if ph < 6 or ph > 8:
    score -= 20

st.metric("💚 System Health", score)

# =========================
# EFFICIENCY SCORE
# =========================
st.markdown("## ⚡ Efficiency")

efficiency = 100

if oxygen < 5:
    efficiency -= 30
if water_temp > 30:
    efficiency -= 20
if ph < 6 or ph > 8:
    efficiency -= 20
if humidity < 40:
    efficiency -= 10

st.metric("⚡ Efficiency Score", f"{efficiency}%")

# =========================
# ALERTS
# =========================
st.markdown("## 🚨 Alerts")

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
# AUTO CONTROL
# =========================
st.markdown("## 🤖 Auto Control")

pump_status = "OFF"
fan_status = "OFF"

if oxygen < 5:
    send_to_blynk("v10", 1)
    pump_status = "ON"
else:
    send_to_blynk("v10", 0)

if water_temp > 30:
    send_to_blynk("v11", 1)
    fan_status = "ON"
else:
    send_to_blynk("v11", 0)

col1, col2 = st.columns(2)
col1.metric("🫧 Air Pump", pump_status)
col2.metric("🌬 Fan", fan_status)

# =========================
# MANUAL CONTROL
# =========================
st.markdown("## 🎮 Manual Control")

col1, col2 = st.columns(2)

with col1:
    if st.button("Pump ON", key="p_on"):
        send_to_blynk("v10", 1)
    if st.button("Pump OFF", key="p_off"):
        send_to_blynk("v10", 0)

with col2:
    if st.button("Fan ON", key="f_on"):
        send_to_blynk("v11", 1)
    if st.button("Fan OFF", key="f_off"):
        send_to_blynk("v11", 0)

# =========================
# CHARTS
# =========================
st.markdown("## 📈 Live Trends")
st.line_chart(df.set_index("time")[["water_temp", "ph", "oxygen"]])

# =========================
# AI ANOMALY DETECTION
# =========================
st.markdown("## 🧠 AI Detection")

def detect_anomaly(values):
    if len(values) < 5:
        return False
    mean = np.mean(values)
    std = np.std(values)
    if std == 0:
        return False
    return abs(values[-1] - mean) / std > 2

oxygen_list = [x["oxygen"] for x in st.session_state.history]
temp_list = [x["water_temp"] for x in st.session_state.history]
ph_list = [x["ph"] for x in st.session_state.history]

if detect_anomaly(oxygen_list):
    st.error("Oxygen anomaly detected")

if detect_anomaly(temp_list):
    st.error("Temperature anomaly detected")

if detect_anomaly(ph_list):
    st.error("pH anomaly detected")

if not (detect_anomaly(oxygen_list) or detect_anomaly(temp_list) or detect_anomaly(ph_list)):
    st.success("System Normal")

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Smart IoT + AI + Automation System")