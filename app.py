import streamlit as st
import joblib
import pandas as pd

from automation import automation_control
from database import save_data, get_data
from simulation import generate_sensor_data
from report import generate_pdf

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="Smart Aquaponics AI System",
    layout="wide"
)

# ==============================
# UI POLISH (Professional Look)
# ==============================

st.markdown("""
<style>
body {
    background-color: #0e1117;
}

div[data-testid="metric-container"] {
    background-color: #1c1f26;
    border-radius: 12px;
    padding: 15px;
    box-shadow: 0px 0px 10px rgba(0,0,0,0.4);
}

h1, h2, h3 {
    color: #4CAF50;
}

.stButton>button {
    background-color: #4CAF50;
    color: white;
    border-radius: 8px;
    padding: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🌱 Smart Aquaponics AI System")

st.markdown("""
### 🌿 Smart Farming Control Center
AI • IoT Simulation • Automation • Real-time Monitoring
""")

st.markdown("🟢 System Live Status: ACTIVE")
st.progress(100)

# ==============================
# LOGIN SYSTEM
# ==============================

users = {
    "admin": "1234",
    "engineer": "iot2026"
}

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "login_error" not in st.session_state:
    st.session_state.login_error = ""

if not st.session_state.logged_in:

    st.subheader("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.session_state.login_error = "❌ Invalid credentials"

    with col2:
        if st.button("Reset"):
            st.session_state.logged_in = False
            st.session_state.login_error = ""
            st.rerun()

    if st.session_state.login_error:
        st.error(st.session_state.login_error)

    st.stop()

# ==============================
# LOAD MODELS
# ==============================

plant_model = joblib.load("plant_health_model.pkl")
fish_model = joblib.load("fish_health_model.pkl")

# ==============================
# SENSOR DATA
# ==============================

data = generate_sensor_data()
save_data(data)

# ==============================
# AI PREDICTIONS
# ==============================

plant_input = pd.DataFrame([[
    data['water_temp'],
    data['ph'],
    data['oxygen'],
    data['humidity']
]], columns=["water_temp", "ph", "oxygen", "humidity"])

plant_prediction = plant_model.predict(plant_input)[0]

fish_input = pd.DataFrame([[
    data['water_temp'],
    data['ph'],
    data['oxygen']
]], columns=["water_temp", "ph", "oxygen"])

fish_prediction = fish_model.predict(fish_input)[0]

# ==============================
# AUTOMATION
# ==============================

devices = automation_control(data)

# ==============================
# ALERT SYSTEM
# ==============================

alerts = []

if data["oxygen"] < 5:
    alerts.append("Low Oxygen Level")

if data["ph"] < 6 or data["ph"] > 8:
    alerts.append("pH Out of Safe Range")

if data["water_temp"] > 30:
    alerts.append("High Water Temperature")

if fish_prediction != "Healthy":
    alerts.append("Fish Health Risk Detected")

# ==============================
# SYSTEM SCORE
# ==============================

score = 100

if data["oxygen"] < 5:
    score -= 25
if data["ph"] < 6 or data["ph"] > 8:
    score -= 25
if data["water_temp"] > 30:
    score -= 20
if fish_prediction != "Healthy":
    score -= 30

status = "🟢 Healthy"
if score < 80:
    status = "🟡 Warning"
if score < 50:
    status = "🔴 Critical"

# ==============================
# DASHBOARD HEADER
# ==============================

col1, col2, col3, col4 = st.columns(4)

col1.metric("System Status", status)
col2.metric("Health Score", f"{score}/100")
col3.metric("Plant", plant_prediction)
col4.metric("Fish", fish_prediction)

st.divider()

# ==============================
# SENSOR DATA
# ==============================

st.subheader("📡 Live Sensor Data")

c1, c2, c3 = st.columns(3)
c1.metric("Water Temp", f"{data['water_temp']} °C")
c2.metric("pH", data['ph'])
c3.metric("Oxygen", f"{data['oxygen']} mg/L")

c4, c5, c6 = st.columns(3)
c4.metric("Humidity", f"{data['humidity']} %")
c5.metric("Air Temp", f"{data['air_temp']} °C")
c6.metric("Water Level", f"{data['water_level']} %")

st.divider()

# ==============================
# AI ANALYSIS
# ==============================

st.subheader("🧠 AI Analysis")

colA, colB = st.columns(2)

with colA:
    st.markdown("### 🌱 Plant Health")
    if plant_prediction == "Healthy":
        st.success(plant_prediction)
    elif plant_prediction == "Warning":
        st.warning(plant_prediction)
    else:
        st.error(plant_prediction)

with colB:
    st.markdown("### 🐟 Fish Health")
    if fish_prediction == "Healthy":
        st.success(fish_prediction)
    elif fish_prediction == "Stress":
        st.warning(fish_prediction)
    else:
        st.error(fish_prediction)

st.divider()

# ==============================
# AUTOMATION
# ==============================

st.subheader("⚙️ Automation System")

a1, a2, a3, a4 = st.columns(4)

a1.write(f"Air Pump: {devices['air_pump']}")
a2.write(f"Water Pump: {devices['water_pump']}")
a3.write(f"Cooling Fan: {devices['cooling_fan']}")
a4.write(f"Grow Light: {devices['grow_light']}")

st.divider()

# ==============================
# ALERTS
# ==============================

st.subheader("🚨 Smart Alerts")

if len(alerts) == 0:
    st.success("System Stable - No Alerts")
else:
    for a in alerts:
        st.warning("⚠️ " + a)

st.divider()

# ==============================
# AI INSIGHTS
# ==============================

st.subheader("🧠 AI Insights")

if plant_prediction == "Healthy" and fish_prediction == "Healthy":
    st.success("System is operating at optimal efficiency")

if data["oxygen"] < 5:
    st.warning("Low oxygen may reduce fish growth")

if data["water_temp"] > 30:
    st.warning("High temperature affects system stability")

st.divider()

# ==============================
# RECOMMENDATIONS
# ==============================

st.subheader("💡 Recommendations")

if data["oxygen"] < 5:
    st.info("Turn ON Air Pump immediately")

if data["ph"] < 6:
    st.info("Increase pH level")
elif data["ph"] > 8:
    st.info("Decrease pH level")

if data["water_temp"] > 30:
    st.info("Activate cooling system")

st.divider()

# ==============================
# ANALYTICS
# ==============================

st.subheader("📊 Analytics")

history = get_data()

df = pd.DataFrame(history, columns=[
    "ID",
    "Water Temp",
    "Air Temp",
    "Humidity",
    "pH",
    "Oxygen",
    "Water Level"
])

st.line_chart(df[["Water Temp", "Oxygen", "pH"]])

st.divider()

# ==============================
# SYSTEM SUMMARY
# ==============================

st.subheader("📄 System Summary")

summary = {
    "Plant Status": plant_prediction,
    "Fish Status": fish_prediction,
    "System Score": score,
    "Alerts": len(alerts)
}

st.json(summary)

st.divider()

# ==============================
# PDF REPORT
# ==============================

st.subheader("📄 Report Generator")

if st.button("Generate PDF Report"):
    file = generate_pdf(
        data=data,
        plant_status=plant_prediction,
        fish_status=fish_prediction,
        alerts=alerts
    )

    with open(file, "rb") as f:
        st.download_button(
            "⬇️ Download Report",
            f,
            file_name="aquaponics_report.pdf",
            mime="application/pdf"
        )