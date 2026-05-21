import requests
import time
from simulation import generate_sensor_data

# =====================================================
# BLYNK AUTH TOKEN
# =====================================================
BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"

# =====================================================
# SEND DATA TO BLYNK
# =====================================================
def send(pin, value):

    url = f"https://blynk.cloud/external/api/update?token={BLYNK_AUTH}&{pin}={value}"

    try:
        requests.get(url)
    except:
        print(f"❌ Failed to send data to {pin}")

# =====================================================
# SEND BLYNK EVENTS (NOTIFICATIONS)
# =====================================================
def trigger_event(event_name, description):

    url = (
        f"https://blynk.cloud/external/api/logEvent?"
        f"token={BLYNK_AUTH}"
        f"&event={event_name}"
        f"&description={description}"
    )

    try:
        requests.get(url)
        print(f"🔔 Event Triggered: {event_name}")

    except:
        print(f"❌ Failed Event: {event_name}")

# =====================================================
# AI CONTROL SYSTEM
# =====================================================
def ai_control(data):

    actions = {
        "air_pump": 0,
        "fan": 0,
        "alerts": []
    }

    # =========================================
    # LOW OXYGEN DETECTION
    # =========================================
    if data["oxygen"] < 5:

        actions["air_pump"] = 1

        actions["alerts"].append(
            "⚠️ Low Oxygen Level"
        )

        trigger_event(
            "low_oxygen",
            "Oxygen level is critically low"
        )

    # =========================================
    # HIGH TEMPERATURE DETECTION
    # =========================================
    if data["water_temp"] > 30:

        actions["fan"] = 1

        actions["alerts"].append(
            "⚠️ High Water Temperature"
        )

        trigger_event(
            "high_temp",
            "Water temperature is too high"
        )

    # =========================================
    # PH ALERT
    # =========================================
    if data["ph"] < 6:

        actions["alerts"].append(
            "⚠️ pH Too Low"
        )

        trigger_event(
            "ph_alert",
            "pH level is too low"
        )

    elif data["ph"] > 8:

        actions["alerts"].append(
            "⚠️ pH Too High"
        )

        trigger_event(
            "ph_alert",
            "pH level is too high"
        )

    return actions

# =====================================================
# SYSTEM START
# =====================================================
print("🚀 Smart Aquaponics AI System Started")

loop = 0

# =====================================================
# MAIN LOOP
# =====================================================
while True:

    loop += 1

    print(f"\n🔄 LOOP #{loop}")

    # =========================================
    # GENERATE SENSOR DATA
    # =========================================
    data = generate_sensor_data()

    print("\n📡 SENSOR DATA")
    print(data)

    # =========================================
    # SEND SENSOR DATA TO BLYNK
    # =========================================
    send("v0", data["water_temp"])
    send("v1", data["ph"])
    send("v2", data["oxygen"])
    send("v3", data["humidity"])
    send("v4", data["air_temp"])
    send("v5", data["water_level"])

    print("\n✅ Sensor Data Sent To Blynk")

    # =========================================
    # AI CONTROL
    # =========================================
    actions = ai_control(data)

    # =========================================
    # SEND AI CONTROLS
    # =========================================
    send("v10", actions["air_pump"])
    send("v11", actions["fan"])

    # =========================================
    # PRINT AI STATUS
    # =========================================
    print("\n🤖 AI CONTROL STATUS")

    if actions["air_pump"] == 1:
        print("🟢 Air Pump: ON")
    else:
        print("⚪ Air Pump: OFF")

    if actions["fan"] == 1:
        print("🟢 Cooling Fan: ON")
    else:
        print("⚪ Cooling Fan: OFF")

    # =========================================
    # ALERTS
    # =========================================
    print("\n🚨 ALERTS")

    if len(actions["alerts"]) == 0:

        print("✅ System Stable")

    else:

        for alert in actions["alerts"]:
            print(alert)

    # =========================================
    # SYSTEM HEALTH SCORE
    # =========================================
    score = 100

    if data["oxygen"] < 5:
        score -= 30

    if data["water_temp"] > 30:
        score -= 25

    if data["ph"] < 6 or data["ph"] > 8:
        score -= 20

    # =========================================
    # HEALTH STATUS
    # =========================================
    if score >= 80:
        health_status = "🟢 HEALTHY"

    elif score >= 50:
        health_status = "🟡 WARNING"

    else:
        health_status = "🔴 CRITICAL"

    print(f"\n💚 SYSTEM HEALTH SCORE: {score}/100")
    print(f"📊 SYSTEM STATUS: {health_status}")

    # =========================================
    # SEND STATUS TO BLYNK
    # =========================================
    send("v12", score)

    # =========================================
    # WAIT
    # =========================================
    time.sleep(2)