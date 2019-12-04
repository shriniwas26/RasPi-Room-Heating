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
from configuration import *

# First part of the actual command:
# "cometblue -f json device -p 1762 80:30:DC:E9:4E:50" + " get temperatures"
BASE_COMMAND_WRITE = "cometblue device -p 1762 {}".format(BT_MAC_ADDR)
BASE_COMMAND_READ = BASE_COMMAND_WRITE.replace(
    "cometblue", "cometblue -f json")  # Read values in JSON format


def setup_logger():
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)
    # for level in range(logging.DEBUG, logging.CRITICAL + 10, 10):
    #     logging.addLevelName(level, '[{}]'.format(logging.getLevelName(level)))

    # Define format
    formatter = logging.Formatter(
        "%(asctime)s :: %(levelname)-5s :: %(funcName)17s() :: %(message)s")
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
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def run_command(command):
    logger = logging.getLogger("root")
    logger.debug("Running command: '{}'".format(command))
    result = subprocess.run([command], stdout=subprocess.PIPE, shell=True)
    if result.returncode != 0:
        error_message = "Command '{}' failed!".format(command)
        logger.error(error_message)
        raise RuntimeError(error_message)
    return result.stdout


def get_current_timeslot(active_timeslots):
    for timeslot in active_timeslots:
        if timeslot["start"] < dt.datetime.now() < timeslot["end"]:
            return timeslot
    return None


def get_slots_for_day(all_active_timeslots, date_x):
    active_timeslots = all_active_timeslots[date_x.weekday()]
    # Filter out invalid timeslots: null and empty ones
    valid_timeslots = list(
        filter(lambda t: (t["start"] != t["end"] != None), active_timeslots))

    def timeslot_to_datetime(timeslot):
        formatted_timeslot = {}
        for key in ["start", "end"]:
            value = timeslot[key]
            time_x = dt.datetime.strptime(value, "%H:%M:%S").time()
            date_time = dt.datetime.combine(date_x, time_x)
            formatted_timeslot[key] = date_time
        return formatted_timeslot
    return list(map(timeslot_to_datetime, valid_timeslots))


def timeslot_to_str(ts):
    return "{} -> {}".format(ts["start"], ts["end"])


def restore_config():
    logger = logging.getLogger("root")
    config_file = os.path.split(os.path.abspath(__file__))[0] + "/config.json"
    logger.info("Config file: {}".format(config_file))
    run_command(BASE_COMMAND_WRITE + " restore " + config_file)
    logger.info("Config restored successfully")


def main():
    setup_logger()
    logger = logging.getLogger("root")
    while True:
        # Write "good" config
        restore_config()

        # Log battery level
        logger.info("Getting battery information from thermostat...")
        result_stdout = run_command(BASE_COMMAND_READ + " get battery")
        battery_level = result_stdout.decode("utf-8")
        logger.info("Battery = {} %".format(battery_level))

        # Ensure correct time is set on cometblue
        logger.info("Setting time on cometblue...")
        run_command(BASE_COMMAND_WRITE + " set datetime")
        logger.info("Time set successfully")

        # Read timeslots
        logger.info("Reading active timeslots from cometblue...")
        result_stdout = run_command(BASE_COMMAND_READ + " get days")
        all_active_timeslots = json.loads(result_stdout)
        today = dt.date.today()
        tomorrow = dt.date.today() + dt.timedelta(days=1)
        # Add one extra slot from next day
        active_timeslots = \
            get_slots_for_day(all_active_timeslots, today) + \
            get_slots_for_day(all_active_timeslots, tomorrow)[:1]
        logger.info("Active timeslots: \n{}".format(
            pprint.pformat(list(map(timeslot_to_str, active_timeslots)))))

        current_timeslot = get_current_timeslot(active_timeslots)
        if current_timeslot is None:
            # Step(1): Set the offset temperature to 0'C and setpoint to 10'C
            run_command(BASE_COMMAND_WRITE +
                        " set temperatures --temp-offset 0")
            run_command(BASE_COMMAND_WRITE +
                        " set temperatures --temp-target-high 10")
            run_command(BASE_COMMAND_WRITE +
                        " set temperatures --temp-manual 10")

            # Step(2): Find immediate next timeslot
            upcoming_timeslots = filter(
                lambda ts: ts["start"] > dt.datetime.now(), active_timeslots)
            upcoming_starting_times = map(
                lambda ts: ts["start"], upcoming_timeslots)
            next_start_time = min(upcoming_starting_times)

            # Step(3): Sleep for the difference
            time_to_sleep = next_start_time - dt.datetime.now().replace(microsecond=0)
            logger.info(
                "Next active timeslot starts at: {}".format(next_start_time))
            logger.info(
                "Sleeping for {} ...".format(time_to_sleep))
            time.sleep(time_to_sleep.total_seconds())

        else:
            # Start the monitoring loop
            logger.info("Current active timeslot is: [{}]".format(
                timeslot_to_str(current_timeslot)))
            monitoring_loop(current_timeslot)
            logger.info("Timeslot [{}] ended".format(
                timeslot_to_str(current_timeslot)))
            # After the while loop, write the JSON config again
            restore_config()


def monitoring_loop(current_timeslot):
    logger = logging.getLogger("root")
    while dt.datetime.now() < current_timeslot["end"]:
        logger.info("Running loop for the slot [{}]".format(
            timeslot_to_str(current_timeslot)))
        """ Step (1) """
        sensor_data_file = "/tmp/dht22_reading.txt"
        with open(sensor_data_file) as f:
            logger.info(
                "Read DHT22 sensor file: '{}'".format(sensor_data_file))
            lines = f.readlines()
            dht22_temp = float(lines[0])
            dht22_hum = float(lines[1])
        logger.info(
            "DHT22 sensor reports: Temp = {:.2f} C, Hum = {:.2f} %".format(dht22_temp, dht22_hum))

        """ Step (2) """
        logger.info("Reading temperature from cometblue...")
        result_stdout = run_command(BASE_COMMAND_READ + " get temperatures")
        cometblue_temperatures = json.loads(result_stdout)
        logger.info("All temperatures: \n{}".format(
            pprint.pformat(cometblue_temperatures)))
        logger.info("Cometblue reports: {} C".format(
            cometblue_temperatures["current_temp"]))

        """ Step (3) """
        correct_offset = round(
            dht22_temp - cometblue_temperatures["current_temp"])
        logger.info("Correct offset is: {} C".format(correct_offset))

        if cometblue_temperatures["offset_temp"] != correct_offset:
            logger.info("Setting correct offset...")
            run_command(
                BASE_COMMAND_WRITE +
                " set temperatures --temp-offset {}".format(correct_offset))
            result_stdout = run_command(
                BASE_COMMAND_READ + " get temperatures")
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
