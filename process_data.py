#!/usr/bin/env python3

import matplotlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.cbook as cbook

import numpy as np
import datetime as dt
import sys
import re


if __name__ == "__main__":
    with open(sys.argv[1]) as f:
        line_list = f.readlines()


    regexp = re.compile("DHT22.*Temperature = ([0-9]*.[0-9])")

    data = []

    for line in line_list:
        match = re.search(regexp, line)
        if match is not None:
            line = line.replace("\x00", "")
            # print(line.rstrip("\n"))
            split_line = line.split()
            date_time_string = " ".join(split_line[0:2])
            mtime = dt.datetime.strptime(date_time_string, "%Y-%m-%d %H:%M:%S.%f")
            temperature = float(match.group(1))
            data.append((mtime, temperature))



    months = mdates.MonthLocator()  # every month

    fig, ax = plt.subplots()

    # ax.xaxis.set_major_locator(mdates.DayLocator())

    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d %Hh'))


    ax.set_ylim(0, 30)
    x, y1 = zip(*data)
    ax.plot(x, y1, 'b-')
    ax.grid()

    fig.autofmt_xdate()

    fig.savefig("test.png")
    plt.show()
