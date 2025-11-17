# stepper_class_shiftregister_multiprocessing.py
#
# Stepper class

import time
import multiprocessing
from multiprocessing import Value
from shifter import Shifter


class Stepper:

    # ===== CLASS ATTRIBUTES =====
    num_steppers = 0
    shifter_outputs = Value('i', 0)   # shared shift-register output
    seq = [0b0001,0b0011,0b0010,0b0110,
           0b0100,0b1100,0b1000,0b1001]   # CCW sequence
    delay = 1200
    steps_per_degree = 4096/360


    # ===== INITIALIZATION =====
    def __init__(self, shifter, lock):
        self.s = shifter
        self.angle = Value('d', 0.0)      # shared angle
        self.step_state = 0
        self.shifter_bit_start = 4 * Stepper.num_steppers  # Motor1 = bits 0–3
        self.lock = lock

        Stepper.num_steppers += 1


    # ===== SIGN FUNCTION =====
    def __sgn(self, x):
        if x == 0: return 0
        return int(abs(x)/x)


    # ===== ONE STEP =====
    def __step(self, dir):

        self.step_state = (self.step_state + dir) % 8
        seq_bits = Stepper.seq[self.step_state] << self.shifter_bit_start

        # === RESTORE ORIGINAL WORKING BIT LOGIC ===
        with self.lock:
            val = Stepper.shifter_outputs.value

            # 1. OR: activate this motor’s 4 bits
            val &= ~(0b1111 << self.shifter_bit_start)

            # 2. AND: write actual step pattern
            val |= seq_bits

            Stepper.shifter_outputs.value = val
            self.s.shiftByte(val)

        # update angle
        self.angle.value = (self.angle.value +
                            dir / Stepper.steps_per_degree) % 360


    # ===== ROTATE WORKER =====
    def __rotate(self, delta):
        self.lock.acquire()
        numSteps = int(Stepper.steps_per_degree * abs(delta))
        dir = self.__sgn(delta)
        for _ in range(numSteps):
            self.__step(dir)
            time.sleep(Stepper.delay/1e6)
        self.lock.release()


    # ===== PUBLIC ROTATE =====
    def rotate(self, delta):
        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()
        return p


    # ===== GO TO ABSOLUTE ANGLE =====
    def goAngle(self, angle):
        cur = self.angle.value
        delta = angle - cur

        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360

        return self.rotate(delta)


    # ===== ZERO =====
    def zero(self):
        self.angle.value = 0.0



# ===== EXAMPLE USE =====
if __name__ == '__main__':

    s = Shifter(data=16, latch=20, clock=21)
    lock = multiprocessing.Lock()

    m1 = Stepper(s, lock)   # Motor 1 = ABCD (bits 0–3)
    m2 = Stepper(s, lock)   # Motor 2 = next 4 bits

    m1.zero()
    m2.zero()

    m1.rotate(90)
    m2.rotate(-90)

    try:
        while True:
            pass
    except:
        print("\nend")
