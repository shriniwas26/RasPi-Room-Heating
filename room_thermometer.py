#!/usr/bin/env python3
from sense_hat import SenseHat
import time
import sense_hat_display_number
import logging
import logging.handlers
import os
import Adafruit_DHT
import datetime
import time

CYCLE_SLEEP = 2
INTENSITY = 50

# DHT Sensor Config
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4


def setup_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # Define format
    formatter = logging.Formatter('%(asctime)s %(message)s')
    formatter.default_msec_format = '%s.%03d'

    # Setup file handler
    dirname, _filename = os.path.split(os.path.abspath(__file__))
    fh_info = logging.handlers.TimedRotatingFileHandler(
        dirname + "/logs/room_weather.log", when='midnight', backupCount=50)
    fh_info.setLevel(logging.INFO)
    fh_info.setFormatter(formatter)
    logger.addHandler(fh_info)

    # Setup ch
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def main():
    sense = SenseHat()
    sense.set_rotation(270)
    sense.clear()
    logger = setup_logger()
    dn = sense_hat_display_number.NumberDisplay(rotation=270)
    color_temp = [INTENSITY, 0, 0]
    color_hum  = [0, INTENSITY, 0]
    square_shape = [(x, y) for x in range(2) for y in range(2)]
    while True:
        t1 = time.time() # To compensate for time lost in sensor and file I/O
        """ Read from the DHT22 sensor """
        humidity_dht22, temperature_dht22 = Adafruit_DHT.read_retry(
            DHT_SENSOR, DHT_PIN)
        logger.info("[DHT22] Temperature = {:0.1f} C".format(
            temperature_dht22))
        logger.info("[DHT22] Humidity    = {:0.0f} %".format(humidity_dht22))

        # Read from the sensors on Sense-Hat
        humidity_sense = sense.get_humidity()
        temperature_sense = sense.get_temperature()
        pressure = sense.get_pressure()
        logger.info("[SenseHat] Temperature = {:.1f} C".format(temperature_sense))
        logger.info("[SenseHat] Humidity    = {:.0f} %".format(humidity_sense))
        logger.info("[SenseHat] Pressure    = {:.0f} millibar".format(pressure))

        # Write date to temp files (for use by other programs)
        with open("/tmp/temperature_dht22.txt", "w") as fh:
            fh.write("{}\n".format(temperature_dht22))

        with open("/tmp/temperature_sense_hat.txt", "w") as fh:
            fh.write("{}\n".format(temperature_sense))

        logger.info("-" * 50)

        # Only sleep for (cycle time - time spent in IO),
        # so that transitions appear smooth
        delta = CYCLE_SLEEP - (time.time() - t1)
        logger.info("Sleeping for {:.4f} seconds".format(delta))
        time.sleep(max(0, delta))

        # Display Sense-Hat Temperature/Humidity
        sense.clear()
        for x, y in square_shape:
            sense.set_pixel(x, y, INTENSITY, INTENSITY, INTENSITY)
        dn.show_number(round(temperature_sense), *color_temp)
        time.sleep(CYCLE_SLEEP)
        dn.show_number(round(humidity_sense), *color_hum)
        time.sleep(CYCLE_SLEEP)

        # Display DHT22 Temperature/Humidity
        sense.clear()
        for x, y in square_shape:
            sense.set_pixel(7-x, y, INTENSITY, INTENSITY, INTENSITY)
        dn.show_number(round(temperature_dht22), *color_temp)
        time.sleep(CYCLE_SLEEP)
        dn.show_number(round(humidity_dht22), *color_hum)



if __name__ == "__main__":
    error_count = 0
    while True:
        if error_count > 5:
            logging.error("Too many errors, Sleeping...")
            sleep(15 * 60)
        try:
            main()
            error_count = 0
        except Exception as e:
            error_count += 1
            logging.error("Exception {} occured".format(e))
            logging.warn("Retrying...")
