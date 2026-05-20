def automation_control(data):

    devices = {
        "air_pump": "OFF",
        "water_pump": "ON",
        "cooling_fan": "OFF",
        "grow_light": "OFF"
    }

    # Oxygen Control
    if data["oxygen"] < 5:
        devices["air_pump"] = "ON"

    # Water Temperature Control
    if data["water_temp"] > 30:
        devices["cooling_fan"] = "ON"

    # Humidity / Light Control
    if data["humidity"] < 50:
        devices["grow_light"] = "ON"

    return devices