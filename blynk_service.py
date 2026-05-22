import requests
import random
import time

# =========================
# BLYNK TOKEN
# =========================
BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"

BASE_URL = "https://blynk.cloud/external/api/update"

print("✅ Blynk Data Service Running")

# =========================
# SEND FUNCTION
# =========================
def send(pin, value):
    try:
        requests.get(BASE_URL, params={
            "token": BLYNK_AUTH,
            pin: value
        })
    except Exception as e:
        print("Error:", e)

# =========================
# MAIN LOOP
# =========================
while True:

    # =====================
    # SENSOR DATA
    # =====================
    water_temp = round(random.uniform(24, 30), 2)
    ph = round(random.uniform(6.5, 7.5), 2)
    oxygen = round(random.uniform(5, 9), 2)
    humidity = round(random.uniform(40, 70), 2)
    air_temp = round(random.uniform(25, 35), 2)
    water_level = round(random.uniform(50, 100), 2)

    # =====================
    # SEND DATA (SAFE ORDER)
    # =====================
    send("V0", water_temp)
    time.sleep(0.2)

    send("V1", ph)
    time.sleep(0.2)

    send("V2", oxygen)
    time.sleep(0.2)

    send("V3", humidity)
    time.sleep(0.2)

    send("V4", air_temp)
    time.sleep(0.2)

    send("V5", water_level)

    # =====================
    # LOG
    # =====================
    print("📡 Updated All Sensors:")
    print("🌡 Temp:", water_temp)
    print("🧪 pH:", ph)
    print("🫧 Oxygen:", oxygen)
    print("💧 Humidity:", humidity)
    print("🌬 Air:", air_temp)
    print("🚰 Water:", water_level)
    print("------------------------")

    time.sleep(2)