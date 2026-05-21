import streamlit as st
import time
import pandas as pd
from simulation import generate_sensor_data

st.set_page_config(page_title="Smart Aquaponics AI Dashboard", layout="wide")

st.title("🌱 Smart Aquaponics AI Dashboard")

# تخزين البيانات
if "history" not in st.session_state:
    st.session_state.history = []

# AI logic (نفس الفكرة)
def ai_control(data):

    alert = []

    if data["oxygen"] < 5:
        alert.append("Low Oxygen")

    if data["water_temp"] > 30:
        alert.append("High Temperature")

    if data["ph"] < 6 or data["ph"] > 8:
        alert.append("pH Out of Range")

    return alert

placeholder = st.empty()

while True:

    data = generate_sensor_data()

    alerts = ai_control(data)

    st.session_state.history.append(data)

    df = pd.DataFrame(st.session_state.history)

    with placeholder.container():

        col1, col2, col3 = st.columns(3)

        col1.metric("Water Temp", data["water_temp"])
        col2.metric("pH", data["ph"])
        col3.metric("Oxygen", data["oxygen"])

        st.subheader("🤖 AI Alerts")

        if len(alerts) == 0:
            st.success("System Stable 🟢")
        else:
            for a in alerts:
                st.warning(a)

        st.subheader("📊 Live Trends")

        st.line_chart(df[["water_temp", "ph", "oxygen"]])

    time.sleep(2)