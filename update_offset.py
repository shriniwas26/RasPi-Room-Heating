#!/usr/bin/env python3
import subprocess
import time
import logging
import logging.handlers
import os
import json
import sys
import random
import pprint

# First part of the actual command:
# `cometblue -f json device -p 1762 80:30:DC:E9:4E:50 get temperatures`
BASE_COMMAND = "cometblue -f json device -p 1762 80:30:DC:E9:4E:50"
SLEEP_MINUTES = 10


def get_logger():
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)

    # Define format
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s")
    formatter.default_time_format = "%Y-%m-%d %H:%M:%S"
    formatter.default_msec_format = "%s.%03d"

    # Setup file handler
    dirname, _filename = os.path.split(os.path.abspath(__file__))
    fh_info = logging.handlers.TimedRotatingFileHandler(
        dirname + "/logs/update_offset.log", when='midnight', backupCount=50)
    fh_info.setLevel(logging.DEBUG)
    fh_info.setFormatter(formatter)
    logger.addHandler(fh_info)

    # Setup console logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def run_command(command):
    logger = logging.getLogger("root")
    logger.debug("Running command: '{}'".format(command))
    result = subprocess.run([command], stdout=subprocess.PIPE, shell=True)
    if result.returncode != 0:
        logger.error("Command '{}' failed!".format(command))
        raise RuntimeError("Command '{}' failed!".format(command))
    return result.stdout


def main():
    logger = get_logger()
    random.seed(0)
    while True:
        """ Step (1) """
        sensor_data_file = "/tmp/temperature_dht22.txt"
        with open(sensor_data_file) as f:
            logger.info("Read DHT22 sensor file '{}'".format(sensor_data_file))
            line = f.readlines()[0]
            dht22_temp = float(line)
        logger.info(
            "Room temperature sensor reports: {:.2f} C".format(dht22_temp))

        """ Step (2) """
        random_num = random.random()
        logger.debug("Random number = {:.3f}".format(random_num))
        if random_num < 0.10:
            logger.info("Getting battery information from thermostat...")
            result_stdout = run_command(BASE_COMMAND + " get battery")
            battery_level = result_stdout.decode("utf-8")
            logger.info("Battery: {} %".format(battery_level))

        if random_num < 0.05:
            logger.info("Setting time on cometblue...")
            _result_stdout = run_command(BASE_COMMAND + " set datetime")
            logger.info("Time set successfully")

        """ Step (3) """
        logger.info("Reading temperature from cometblue...")
        result_stdout = run_command(BASE_COMMAND + " get temperatures")
        cometblue_temperatures = json.loads(result_stdout)
        logger.info("All temperatures: \n{}".format(
            pprint.pformat(cometblue_temperatures)))
        cometblue_temp = float(cometblue_temperatures["current_temp"])
        logger.info("Cometblue reports: {} C".format(cometblue_temp))

        """ Step (4) """
        correct_offset_raw = dht22_temp - cometblue_temp
        # Round to nearest 0.5
        correct_offset = round(correct_offset_raw * 2) / 2
        logger.info("Correct offset is: {} C".format(correct_offset))

        if cometblue_temperatures["offset_temp"] != correct_offset:
            logger.info("Setting correct offset...")
            _result_stdout = run_command(
                BASE_COMMAND + " set temperatures --temp-offset {}".format(correct_offset))
            logger.info("Successfully set correct offset")
        else:
            logger.info("Offset is already correct")

        # Sleep
        logger.info("Sleeping for {} minutes...".format(SLEEP_MINUTES))
        time.sleep(SLEEP_MINUTES * 60)


if __name__ == "__main__":
    main()
