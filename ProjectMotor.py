# run_steppers_from_json.py
# Integrates Stepper class + periodic example.json parsing and motor motion.
# Assumptions:
#  - turret[*][1] (theta) -> azimuth (motor 1) in degrees
#  - globe[*][1] (theta)  -> altitude (motor 2) in degrees
#  - Shifter.shiftByte(databyte) is MSB-first (see suggested Shifter)

import time
import multiprocessing
import json
import os
from multiprocessing import Value
from shifter import Shifter
# If your file is named stepper_class_shiftregister_multiprocessing.py,
# you can import Stepper from it; for convenience the Stepper class is included below.

class Stepper:
    """Minimal multiprocessing-safe stepper using shift register (integrated)."""

    num_steppers = 0
    shifter_outputs = Value('i', 0)
    seq = [0b0001, 0b0011, 0b0010, 0b0110,
           0b0100, 0b1100, 0b1000, 0b1001]
    delay = 1200
    steps_per_degree = 4096.0 / 360.0

    def __init__(self, shifter, lock):
        self.s = shifter
        self.angle = Value('d', 0.0)
        self.step_state = 0
        self.shifter_bit_start = 4 * Stepper.num_steppers
        self.lock = lock
        Stepper.num_steppers += 1

    def __sgn(self, x):
        if x == 0:
            return 0
        return int(abs(x) / x)

    def __step(self, dir):
        self.step_state = (self.step_state + dir) % 8
        seq_bits = Stepper.seq[self.step_state] << self.shifter_bit_start

        with self.lock:
            val = Stepper.shifter_outputs.value
            # clear only this motor's nibble, then OR in the pattern
            val &= ~(0b1111 << self.shifter_bit_start)
            val |= seq_bits
            Stepper.shifter_outputs.value = val
            self.s.shiftByte(val)

        self.angle.value = (self.angle.value +
                            dir / Stepper.steps_per_degree) % 360

    def __rotate(self, delta):
        numSteps = int(Stepper.steps_per_degree * abs(delta))
        dir = self.__sgn(delta)
        # Acquire lock for whole rotate to avoid interleaved steps if you prefer
        # a single motor to run uninterrupted. Remove lock.acquire/release if you want
        # fine-grained interleaving (then __step() already uses lock).
        self.lock.acquire()
        try:
            for _ in range(numSteps):
                self.__step(dir)
                time.sleep(Stepper.delay / 1e6)
        finally:
            self.lock.release()

    def rotate(self, delta):
        time.sleep(0.05)
        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()
        return p

    def goAngle(self, target_angle):
        current = self.angle.value
        delta = target_angle - current
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360
        return self.rotate(delta)

    def zero(self):
        self.angle.value = 0.0


# ---------- JSON parsing and motor control logic ----------

EXAMPLE_JSON = "example.json"    # file read repeatedly (for testing)
POLL_INTERVAL = 2.0              # seconds between file checks
LAST_MTIME = 0

def read_positions_from_json(filename=EXAMPLE_JSON):
    """
    Returns (azimuth_deg, altitude_deg) or None on parse error.
    Uses turret[0].theta and globe[0].theta by default.
    """
    if not os.path.isfile(filename):
        return None

    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("JSON read error:", e)
        return None

    try:
        # Build lists similarly to your parse_json()
        turret = [[item['r'], item['theta']] for item in data.get('turrets', {}).values()]
        globe  = [[g['r'], g['theta'], g.get('z', 0)] for g in data.get('globes', [])]

        # Safeguard: require at least one turret and one globe
        if len(turret) == 0 or len(globe) == 0:
            return None

        azimuth = float(turret[0][1])   # degrees
        altitude = float(globe[0][1])   # degrees

        # Clamp/normalize to [0,360)
        azimuth = azimuth % 360.0
        altitude = altitude % 360.0

        return (azimuth, altitude)
    except Exception as e:
        print("JSON parse error:", e)
        return None


def main_loop():
    # Setup shift register and stepper objects
    s = Shifter(data=16, clock=21, latch=20)  # adjust pins to your wiring
    lock = multiprocessing.Lock()

    m1 = Stepper(s, lock)   # motor 1 (azimuth) -> lowest nibble (bits 0-3)
    m2 = Stepper(s, lock)   # motor 2 (altitude) -> next nibble (bits 4-7)

    m1.zero()
    m2.zero()

    global LAST_MTIME
    try:
        while True:
            # Check file modified time to avoid re-reading unchanged file
            try:
                mtime = os.path.getmtime(EXAMPLE_JSON)
            except OSError:
                mtime = 0

            if mtime != LAST_MTIME:
                LAST_MTIME = mtime
                pos = read_positions_from_json(EXAMPLE_JSON)
                if pos is not None:
                    azimuth_deg, altitude_deg = pos
                    print(f"New target positions — azimuth: {azimuth_deg:.2f}°, altitude: {altitude_deg:.2f}°")

                    # Command motors (they return Process objects)
                    p1 = m1.goAngle(azimuth_deg)
                    p2 = m2.goAngle(altitude_deg)

                    # Wait for both to finish before polling next file (change if you want overlap)
                    p1.join()
                    p2.join()
                    print("Motion complete.")
                else:
                    print("No valid positions found in JSON.")
            time.sleep(POLL_INTERVAL)
    except KeyboardInterrupt:
        print("Exiting main loop.")


if __name__ == "__main__":
    main_loop()
