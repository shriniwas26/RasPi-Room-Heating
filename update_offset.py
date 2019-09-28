#!/usr/bin/env python3
import subprocess
import time
import logging
import logging.handlers
import os
import json

# First part of the actual command:
# `cometblue -f json device -p 1762 80:30:DC:E9:4E:50 get temperatures`
BASE_COMMAND = "cometblue -f json device -p 1762 80:30:DC:E9:4E:50"
SLEEP_MINUTES = 15


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
    fh_info.setLevel(logging.INFO)
    fh_info.setFormatter(formatter)
    logger.addHandler(fh_info)

    # Setup console logger
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def main():
    logger = get_logger()
    error_count = 0
    while True:
        if error_count > 5:
            logger.warn(
                "Error threshold, sleeping for {} minutes".format(SLEEP_MINUTES))
            time.sleep(SLEEP_MINUTES * 60)
        try:
            logger.info("Reading DHT22 sensor...")
            with open("/tmp/temperature_dht22.txt") as f:
                line = f.readlines()[0]
                dht22_temp = float(line)
            logger.info("DHT22 Sensor reports: {} °C".format(dht22_temp))
            logger.info("Getting battery information from cometblue...")
            result = subprocess.run(
                [BASE_COMMAND + ' get battery'], stdout=subprocess.PIPE, shell=True)
            assert result.returncode == 0
            battery_level = result.stdout.decode("utf-8")
            logger.info("Battery: {}".format(battery_level))

            logger.info("Reading from cometblue...")
            result = subprocess.run(
                [BASE_COMMAND + ' get temperatures'], stdout=subprocess.PIPE, shell=True)
            cometblue_temperatures = json.loads(result.stdout)
            logger.info("All temperatures: {}".format(cometblue_temperatures))
            # Extract current temp from result

            cometblue_temp = float(cometblue_temperatures["current_temp"])
            logger.info("Cometblue reports: {} °C".format(cometblue_temp))

            # Calculate correct offset
            correct_offset = dht22_temp - cometblue_temp
            # Round to nearest 0.5
            correct_offset = round(correct_offset * 2) / 2
            logger.info("Correct offset is: {} °C".format(correct_offset))

            if cometblue_temperatures["offset_temp"] != correct_offset:
                logger.info("Setting correct offset...")
                result = subprocess.run(
                    [BASE_COMMAND +
                        ' set temperatures --temp-offset {}'.format(correct_offset)],
                    stdout=subprocess.PIPE, shell=True)
                assert result.returncode == 0
                logger.info("Successfully set correct offset")
            else:
                logger.info("Offset already correct")

            # Sleep
            logger.info("Sleeping for {} minutes...".format(SLEEP_MINUTES))
            time.sleep(SLEEP_MINUTES * 60)

            # Reset error count
            error_count = 0

        except Exception as e:
            error_count += 1
            logger.error("Exception: {}".format(str(e)))
            logger.error("Retrying...")


if __name__ == "__main__":
    main()
