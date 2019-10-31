#!/usr/bin/env python3
from sense_hat import SenseHat
import time


class NumberDisplay(object):
    def __init__(self, rotation=0):
        self.OFFSET_LEFT = 0
        self.OFFSET_TOP = 3
        self.NUMS = [1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1,  # 0
                     0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0,  # 1
                     1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1,  # 2
                     1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1,  # 3
                     1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1,  # 4
                     1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1,  # 5
                     1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1,  # 6
                     1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0,  # 7
                     1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1,  # 8
                     1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1]  # 9

        self.sense = SenseHat()
        self.sense.set_rotation(rotation)

    def show_digit(self, val, xd, yd, r, g, b):
        """Displays a single digit (0-9)"""
        assert isinstance(val, int)
        assert 0 <= val <= 9
        offset = val * 15
        for p in range(offset, offset + 15):
            xt = p % 3
            yt = (p-offset) // 3
            self.sense.set_pixel(
                xt+xd, yt+yd, r*self.NUMS[p], g*self.NUMS[p], b*self.NUMS[p])

    def show_number(self, val, r, g, b):
        """Displays a two-digits positive number (0-99)"""
        assert isinstance(val, int)
        assert 0 <= val <= 99

        abs_val = abs(val)
        tens = abs_val // 10
        units = abs_val % 10
        self.show_digit(tens, self.OFFSET_LEFT, self.OFFSET_TOP, r, g, b)
        self.show_digit(units, self.OFFSET_LEFT+4, self.OFFSET_TOP, r, g, b)


# Main function
def main():
    disp = NumberDisplay()
    for i in range(0, 100):
        disp.show_number(i, 200, 0, 60)
        time.sleep(0.2)
    disp.sense.clear()


if __name__ == '__main__':
    main()
