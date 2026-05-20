from automation import automation_control
from database import save_data, get_data

import streamlit as st
from simulation import generate_sensor_data
import joblib
import pandas as pd

# ==============================
# Load AI Models
# ==============================

plant_model = joblib.load("plant_health_model.pkl")
fish_model = joblib.load("fish_health_model.pkl")

# ==============================
# Page Config
# ==============================

st.set_page_config(page_title="Smart Aquaponics", layout="wide")

st.title("🌱 Smart Aquaponics System")

# ==============================
# Generate Sensor Data
# ==============================

data = generate_sensor_data()

# Save to Database
save_data(data)

# ==============================
# AI - Plant Prediction
# ==============================

plant_input = pd.DataFrame([[
    data['water_temp'],
    data['ph'],
    data['oxygen'],
    data['humidity']
]], columns=["water_temp", "ph", "oxygen", "humidity"])

plant_prediction = plant_model.predict(plant_input)[0]

# ==============================
# AI - Fish Prediction
# ==============================

fish_input = pd.DataFrame([[
    data['water_temp'],
    data['ph'],
    data['oxygen']
]], columns=["water_temp", "ph", "oxygen"])

fish_prediction = fish_model.predict(fish_input)[0]

# ==============================
# Automation System
# ==============================

devices = automation_control(data)

# ==============================
# SMART ALERT SYSTEM
# ==============================

alerts = []

if data["oxygen"] < 5:
    alerts.append("🚨 Oxygen level is LOW! Turn ON Air Pump immediately.")

if data["ph"] < 6.0 or data["ph"] > 8.0:
    alerts.append("⚠️ pH is OUT OF SAFE RANGE!")

if data["water_temp"] > 30:
    alerts.append("🔥 Water temperature is TOO HIGH!")

if fish_prediction == "Stress":
    alerts.append("🐟 Fish is under STRESS! Check water quality.")

# ==============================
# Dashboard Layout
# ==============================

col1, col2, col3 = st.columns(3)

col1.metric("🌡️ Water Temp", f"{data['water_temp']} °C")
col2.metric("🧪 pH", data['ph'])
col3.metric("💨 Oxygen", f"{data['oxygen']} mg/L")

col1.metric("💧 Humidity", f"{data['humidity']} %")
col2.metric("☀️ Air Temp", f"{data['air_temp']} °C")
col3.metric("🚰 Water Level", f"{data['water_level']} %")

# ==============================
# Plant Status
# ==============================

st.subheader("🌿 Plant Health Status")

if plant_prediction == "Healthy":
    st.success(f"✅ {plant_prediction}")

elif plant_prediction == "Warning":
    st.warning(f"⚠️ {plant_prediction}")

else:
    st.error(f"🚨 {plant_prediction}")

# ==============================
# Fish Status
# ==============================

st.subheader("🐟 Fish Health Status")

if fish_prediction == "Healthy":
    st.success(f"✅ {fish_prediction}")

elif fish_prediction == "Stress":
    st.warning(f"⚠️ {fish_prediction}")

else:
    st.error(f"🚨 {fish_prediction}")

# ==============================
# Automation Devices
# ==============================

st.subheader("⚙️ Automation System")

col4, col5 = st.columns(2)

col4.write(f"💨 Air Pump: {devices['air_pump']}")
col4.write(f"💧 Water Pump: {devices['water_pump']}")

col5.write(f"❄️ Cooling Fan: {devices['cooling_fan']}")
col5.write(f"💡 Grow Light: {devices['grow_light']}")

# ==============================
# SMART ALERTS
# ==============================

st.subheader("🚨 Smart Alerts System")

if len(alerts) == 0:
    st.success("✅ System is Stable - No Alerts")
else:
    for alert in alerts:
        st.warning(alert)

# ==============================
# Historical Data
# ==============================

st.subheader("📊 Historical Sensor Data")

history = get_data()

history_df = pd.DataFrame(history, columns=[
    "ID",
    "Water Temp",
    "Air Temp",
    "Humidity",
    "pH",
    "Oxygen",
    "Water Level"
])

st.dataframe(history_df)

# ==============================
# Analytics
# ==============================

st.subheader("📈 Analytics")

st.write("🌡️ Water Temperature")
st.line_chart(history_df["Water Temp"])

st.write("💨 Oxygen")
st.line_chart(history_df["Oxygen"])

st.write("🧪 pH")
st.line_chart(history_df["pH"])