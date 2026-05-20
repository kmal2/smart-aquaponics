import random

def generate_sensor_data():

    data = {
        "water_temp": round(random.uniform(22, 32), 2),
        "air_temp": round(random.uniform(20, 38), 2),
        "humidity": round(random.uniform(40, 90), 2),
        "ph": round(random.uniform(5.5, 8.5), 2),
        "oxygen": round(random.uniform(3, 10), 2),
        "water_level": round(random.uniform(30, 100), 2)
    }

    return data