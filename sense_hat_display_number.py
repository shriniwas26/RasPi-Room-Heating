#!/usr/bin/env python3
from sense_hat import SenseHat
import time

OFFSET_LEFT = 0
OFFSET_TOP = 3

NUMS = [1, 1, 1, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1,  # 0
        0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0,  # 1
        1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 1, 1,  # 2
        1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1,  # 3
        1, 0, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1,  # 4
        1, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 1, 1, 1, 1,  # 5
        1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1,  # 6
        1, 1, 1, 0, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 0,  # 7
        1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1,  # 8
        1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 1]  # 9

sense = SenseHat()
sense.set_rotation(270)
def show_digit(val, xd, yd, r, g, b):
    """Displays a single digit (0-9)"""
    assert isinstance(val, int)
    assert 0 <= val <= 9
    offset = val * 15
    for p in range(offset, offset + 15):
        xt = p % 3
        yt = (p-offset) // 3
        sense.set_pixel(xt+xd, yt+yd, r*NUMS[p], g*NUMS[p], b*NUMS[p])


def show_number(val, r, g, b):
    """Displays a two-digits positive number (0-99)"""
    assert isinstance(val, int)
    assert 0 <= val <= 99

    abs_val = abs(val)
    tens = abs_val // 10
    units = abs_val % 10
    if (abs_val > 9):
        show_digit(tens, OFFSET_LEFT, OFFSET_TOP, r, g, b)
    show_digit(units, OFFSET_LEFT+4, OFFSET_TOP, r, g, b)


# Main function
def main():
    sense.clear()
    for i in range(0, 100):
        show_number(i, 200, 0, 60)
        time.sleep(0.2)
    sense.clear()


if __name__ == '__main__':
    main()
