# run_from_json.py
# Uses lab8.py Stepper class + shifter.py to read example.json and move motors.

import time
import multiprocessing
import json
import os
from math import degrees
from shifter import Shifter
from lab8 import Stepper   # ← YOUR FILE

JSON_FILE = "example.json"
POLL_INTERVAL = 2.0
LAST_MTIME = 0

def read_angles():
    """Reads turret 1 theta and globe[0] theta (both in radians) and returns degrees."""
    if not os.path.isfile(JSON_FILE):
        print("JSON file missing.")
        return None

    try:
        with open(JSON_FILE, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("JSON read error:", e)
        return None

    try:
        t1_rad = float(data["turrets"]["1"]["theta"])
        g1_rad = float(data["globes"][0]["theta"])

        return degrees(t1_rad) % 360, degrees(g1_rad) % 360

    except Exception as e:
        print("JSON parse error:", e)
        return None


def main():
    global LAST_MTIME

    # your shift register pins
    s = Shifter(data=16, latch=20, clock=21)

    lock = multiprocessing.Lock()

    # motors
    m1 = Stepper(s, lock)
    m2 = Stepper(s, lock)

    m1.zero()
    m2.zero()

    print("Watching example.json for updates...\n")

    try:
        while True:

            try:
                mtime = os.path.getmtime(JSON_FILE)
            except:
                mtime = 0

            if mtime != LAST_MTIME:
                LAST_MTIME = mtime

                result = read_angles()
                if result is None:
                    continue

                turret_deg, globe_deg = result

                print(f"New JSON data:")
                print(f"  Motor 1 (turret): {turret_deg:.2f}°")
                print(f"  Motor 2 (globe) : {globe_deg:.2f}°")

                p1 = m1.goAngle(turret_deg)
                p2 = m2.goAngle(globe_deg)

                p1.join()
                p2.join()

                print("Motors finished updating.\n")

            time.sleep(POLL_INTERVAL)

    except KeyboardInterrupt:
        print("\nExiting JSON controller.")


if __name__ == "__main__":
    main()
