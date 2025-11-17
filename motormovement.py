# stepper_class_shiftregister_multiprocessing.py
#
# Stepper class
#
# Because only one motor action is allowed at a time, multithreading could be
# used instead of multiprocessing. However, the GIL makes the motor process run
# too slowly on the Pi Zero, so multiprocessing is needed.

import time
import multiprocessing
from multiprocessing import Value
from shifter import Shifter   # our custom Shifter class


class Stepper:
    """
    Supports operation of an arbitrary number of stepper motors using
    one or more shift registers.

    A class attribute (shifter_outputs) keeps track of all
    shift register output values for all motors.
    """

    # Class attributes:
    num_steppers = 0                # track number of Steppers instantiated
    shifter_outputs = Value('i', 0) # <<< SHARED SHIFT REGISTER OUTPUT VALUE >>>
    seq = [0b0001,0b0011,0b0010,0b0110,
           0b0100,0b1100,0b1000,0b1001]  # CCW sequence
    delay = 1200                    # delay between motor steps [us]
    steps_per_degree = 4096/360     # 4096 steps/rev * 1/360 rev/deg

    def __init__(self, shifter, lock):
        self.s = shifter                      # shift register
        self.angle = Value('d', 0.0)          # <<< SHARED ANGLE >>>
        self.step_state = 0                   # track sequence position
        self.shifter_bit_start = 4 * Stepper.num_steppers
        self.lock = lock                      # multiprocessing lock

        Stepper.num_steppers += 1

    # Signum:
    def __sgn(self, x):
        if x == 0: return 0
        return int(abs(x) / x)

    # Move a single step:
    def __step(self, dir):
        self.step_state = (self.step_state + dir) % 8
        pattern = Stepper.seq[self.step_state] << self.shifter_bit_start

        # === FIXED: SAFE BITWISE UPDATE WITH LOCK ===
        with self.lock:
            val = Stepper.shifter_outputs.value

            # clear this motor's 4 bits
            val &= ~(0b1111 << self.shifter_bit_start)

            # write the new motor pattern
            val |= pattern

            Stepper.shifter_outputs.value = val
            self.s.shiftByte(val)

        # update angle
        self.angle.value = (self.angle.value +
                            dir / Stepper.steps_per_degree) % 360

    # Rotate worker:
    def __rotate(self, delta):
        self.lock.acquire()
        numSteps = int(Stepper.steps_per_degree * abs(delta))
        dir = self.__sgn(delta)
        for _ in range(numSteps):
            self.__step(dir)
            time.sleep(Stepper.delay / 1e6)
        self.lock.release()

    # Public rotation:
    def rotate(self, delta):
        time.sleep(0.1)
        p = multiprocessing.Process(target=self.__rotate, args=(delta,))
        p.start()
        return p  # <<< RETURN PROCESS >>>

    # Absolute angle command:
    def goAngle(self, angle):
        current = self.angle.value
        delta = angle - current

        # shortest angle direction:
        if delta > 180:
            delta -= 360
        elif delta < -180:
            delta += 360

        return self.rotate(delta)

    # Zero the motor:
    def zero(self):
        self.angle.value = 0.0


# Example use:
if __name__ == '__main__':

    s = Shifter(data=16, latch=20, clock=21)

    lock = multiprocessing.Lock()

    m1 = Stepper(s, lock)
    m2 = Stepper(s, lock)

    m1.zero()
    m2.zero()

    # demo moves
    m1.rotate(-90)
    m1.rotate(45)
    m1.rotate(-90)
    m1.rotate(45)

    m2.rotate(180)
    m2.rotate(-45)
    m2.rotate(45)
    m2.rotate(-90)

    try:
        while True:
            pass
    except:
        print('\nend')
