# run_steppers_from_json.py
# Reads example.json (radians), converts to degrees, moves 2 steppers.

import time
import multiprocessing
import json
import os
from math import degrees
from shifter import Shifter
from stepper_class_shiftregister_multiprocessing import Stepper

EXAMPLE_JSON = "example.json"   # file name
POLL_INTERVAL = 2.0             # seconds
LAST_MTIME = 0

def read_positions_from_json():
    """
    Returns (azimuth_deg, altitude_deg) or None.
    - turret "1" theta -> motor 1
    - globe[0] theta   -> motor 2
    """
    if not os.path.isfile(EXAMPLE_JSON):
        print("JSON file missing.")
        return None

    try:
        with open(EXAMPLE_JSON, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("JSON read error:", e)
        return None

    try:
        # ----- Extract turret 1 -----
        t1 = data["turrets"]["1"]
        turret_theta_rad = float(t1["theta"])
        turret_deg = degrees(turret_theta_rad) % 360

        # ----- Extract globe 1 -----
        g1 = data["globes"][0]
        globe_theta_rad = float(g1["theta"])
        globe_deg = degrees(globe_theta_rad) % 360

        return (turret_deg, globe_deg)

    except Exception as e:
        print("JSON parse error:", e)
        return None


def main_loop():

    # Shift register uses pins: data=16, latch=20, clock=21
    s = Shifter(data=16, latch=20, clock=21)
    lock = multiprocessing.Lock()

    # Two motors
    m1 = Stepper(s, lock)   # turret 1
    m2 = Stepper(s, lock)   # globe 0

    m1.zero()
    m2.zero()

    global LAST_MTIME

    print("Monitoring example.json for new target angles...")

    try:
        while True:
            # only re-read JSON if file changed
            try:
                mtime = os.path.getmtime(EXAMPLE_JSON)
            except:
                mtime = 0

            if mtime != LAST_MTIME:
                LAST_MTIME = mtime

                pos = read_positions_from_json()
                if pos is not None:
                    turret_deg, globe_deg = pos

                    print(f"\nNEW JSON VALUES:")
                    print(f"  Turret: {turret_deg:.2f}°")
                    print(f"  Globe : {globe_deg:.2f}°")

                    # Move both motors
                    p1 = m1.goAngle(turret_deg)
                    p2 = m2.goAngle(globe_deg)

                    # wait for both motors to finish
                    p1.join()
                    p2.join()

                    print("Motors finished movement.")
                else:
                    print("Invalid JSON — skipping")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("Exiting.")
