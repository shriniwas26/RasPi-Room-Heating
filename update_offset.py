#!/usr/bin/env python3
import subprocess
import time
import logging
import logging.handlers
import os
import json
import sys
import pprint
import datetime as dt

# First part of the actual command:
# `cometblue -f json device -p 1762 80:30:DC:E9:4E:50 get temperatures`
BT_MAC_ADDR = "80:30:DC:E9:4E:50"
BASE_COMMAND = "cometblue -f json device -p 1762 {}".format(BT_MAC_ADDR)
SLEEP_MINUTES = 10


def setup_logger():
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
        dirname + "/logs/update_offset.log",
        when='midnight',
        backupCount=200)
    fh_info.setLevel(logging.DEBUG)
    fh_info.setFormatter(formatter)
    logger.addHandler(fh_info)

    # Setup console logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
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


def get_current_timeslot(active_timeslots):
    dt_now = dt.datetime.now()
    for timeslot in active_timeslots:
        if timeslot["start"] <= dt_now <= timeslot["end"]:
            return timeslot
    return None


def get_slots_for_day(all_active_timeslots, config_date):
    # Filter out invalid timeslots: null and empty ones
    active_timeslots = all_active_timeslots[config_date.weekday()]
    filtered_active_timeslots = list(
        filter(lambda t: (t["start"] != t["end"] != None), active_timeslots))

    def convert_timeslot(timeslot):
        formatted_timeslot = {}
        for key, value in timeslot.items():
            date_time = dt.datetime.strptime(value, "%H:%M:%S").replace(
                year=config_date.year, month=config_date.month, day=config_date.day)
            formatted_timeslot[key] = date_time
        return formatted_timeslot

    return list(map(convert_timeslot, filtered_active_timeslots))


def timeslot_to_str(ts):
    return "{} - {}".format(ts["start"], ts["end"])


def main():
    setup_logger()
    logger = logging.getLogger("root")
    while True:
        logger.info("Reading active timeslots from cometblue...")
        result_stdout = run_command(BASE_COMMAND + " get days")
        all_active_timeslots = json.loads(result_stdout)
        today = dt.date.today()
        tomorrow = dt.date.today() + dt.timedelta(days=1)
        active_timeslots = get_slots_for_day(
            all_active_timeslots, today) + get_slots_for_day(all_active_timeslots, tomorrow)

        active_timeslots_str = [timeslot_to_str(ts) for ts in active_timeslots]
        logger.info("Active timeslots : {}".format(pprint.pformat(active_timeslots_str)))

        current_timeslot = get_current_timeslot(active_timeslots)
        if current_timeslot is None:
            # Find immediate next timeslot, and sleep for the difference
            timeslot_starting_times = [timeslot["start"]
                                       for timeslot in active_timeslots
                                       if timeslot["start"] > dt.datetime.now()]
            next_timeslot = min(timeslot_starting_times)
            time_to_sleep = next_timeslot - dt.datetime.now().replace(microsecond=0)
            time_to_sleep = time_to_sleep - dt.timedelta
            logger.info(
                "Next active timeslot is starts at: {}".format(next_timeslot))
            logger.info(
                " Sleeping for {} ...".format(time_to_sleep))
            time.sleep(time_to_sleep.total_seconds())
        else:
            current_timeslot_str = "{} - {}".format(
                current_timeslot["start"], current_timeslot["end"])
            logger.info("Current active timeslot is: [{}]".format(
                current_timeslot_str))
            monitoring_loop(current_timeslot["end"])
            logger.info("Timeslot [{}] ended".format(current_timeslot_str))


def monitoring_loop(end_time):
    logger = logging.getLogger("root")
    logger.info("Starting loop, stopping time: {} ...".format(str(end_time)))
    # Log battery level
    logger.info("Getting battery information from thermostat...")
    result_stdout = run_command(BASE_COMMAND + " get battery")
    battery_level = result_stdout.decode("utf-8")
    logger.info("Battery: {} %".format(battery_level))
    # Ensure correct time is set on cometblue
    logger.info("Setting time on cometblue...")
    _result_stdout = run_command(BASE_COMMAND + " set datetime")
    logger.info("Time set successfully")

    while dt.datetime.now() < end_time:
        """ Step (1) """
        sensor_data_file = "/tmp/temperature_dht22.txt"
        with open(sensor_data_file) as f:
            logger.info("Read DHT22 sensor file '{}'".format(sensor_data_file))
            line = f.readlines()[0]
            dht22_temp = float(line)
        logger.info(
            "Room temperature sensor reports: {:.2f} C".format(dht22_temp))

        """ Step (2) """
        logger.info("Reading temperature from cometblue...")
        result_stdout = run_command(BASE_COMMAND + " get temperatures")
        cometblue_temperatures = json.loads(result_stdout)
        logger.info("All temperatures: \n{}".format(
            pprint.pformat(cometblue_temperatures)))
        cometblue_temp = float(cometblue_temperatures["current_temp"])
        logger.info("Cometblue reports: {} C".format(cometblue_temp))

        """ Step (3) """
        correct_offset_raw = dht22_temp - cometblue_temp
        # Round to nearest 0.5
        correct_offset = round(correct_offset_raw * 2) / 2
        logger.info("Correct offset is: {} C".format(correct_offset))

        if cometblue_temperatures["offset_temp"] != correct_offset:
            logger.info("Setting correct offset...")
            _result_stdout = run_command(
                BASE_COMMAND + " set temperatures --temp-offset {}".format(correct_offset))
            result_stdout = run_command(BASE_COMMAND + " get temperatures")
            cometblue_temperatures = json.loads(result_stdout)
            logger.info("Checking if offset is correct...")
            assert correct_offset == cometblue_temperatures["offset_temp"]
            logger.info("Successfully set the correct offset")
        else:
            logger.info("Offset is already correct")

        # Sleep
        logger.info("Sleeping for {} minutes...".format(SLEEP_MINUTES))
        time.sleep(SLEEP_MINUTES * 60)


if __name__ == "__main__":
    main()
