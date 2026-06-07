import requests
import random
import time
import shared_data

BLYNK_AUTH = "05GthB1qrQcqSaToJwwYyruodxK-_WdV"
URL = "https://blynk.cloud/external/api/update"

def send(data):
    try:
        requests.get(URL, params={
            "token": BLYNK_AUTH,
            "V0": data["water_temp"],
            "V1": data["ph"],
            "V2": data["oxygen"],
            "V3": data["humidity"],
            "V4": data["air_temp"],
            "V5": data["water_level"]
        }, timeout=1)
    except:
        pass

print("🚀 Blynk running...")

while True:

    shared_data.DATA.update({
        "water_temp": round(random.uniform(24, 30), 2),
        "ph": round(random.uniform(6.5, 7.5), 2),
        "oxygen": round(random.uniform(5, 9), 2),
        "humidity": round(random.uniform(40, 70), 2),
        "air_temp": round(random.uniform(25, 35), 2),
        "water_level": round(random.uniform(50, 100), 2),
        "timestamp": time.time()
    })

    send(shared_data.DATA)

    time.sleep(1)