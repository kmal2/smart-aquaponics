import random

def generate_sensor_data():
    return {
        "water_temp": round(random.uniform(20, 30), 2),
        "ph": round(random.uniform(6.5, 8.0), 2),
        "oxygen": round(random.uniform(4, 10), 2),
        "humidity": round(random.uniform(40, 80), 2),
        "air_temp": round(random.uniform(22, 35), 2),
        "water_level": round(random.uniform(60, 100), 2)
    }