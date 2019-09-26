#!/usr/bin/env python3
from sense_hat import SenseHat
from time import sleep
import sense_hat_display_number
import logging
import logging.handlers
import os
import Adafruit_DHT
import datetime
import time

CYCLE_SLEEP = 1
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
    ch.setLevel(logging.ERROR)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    return logger


def main():
    sense = SenseHat()
    sense.set_rotation(270)
    sense.clear()
    logger = setup_logger()
    dn = sense_hat_display_number.NumberDisplay(rotation=270)
    while True:
        sense.clear()
        sense.show_letter("R", text_colour=[50]*3)
        t1 = time.time()

        """ Read from the sensors on Sense Hat """
        hum = sense.get_humidity()
        temp = sense.get_temperature()
        logger.info(
            "[SenseHat] Temperature = {:.1f} C, Humidity = {:.0f} %".format(temp, hum))

        pressure = sense.get_pressure()
        logger.info("[SenseHat] Pressure = {:.0f} millibar".format(pressure))

        """ Read from the DHT22 sensor """
        humidity_dht22, temperature_dht22 = Adafruit_DHT.read_retry(
            DHT_SENSOR, DHT_PIN)
        if humidity_dht22 is not None and temperature_dht22 is not None:
            logger.info("[DHT22] Temperature = {:0.1f} C, Humidity = {:0.0f} %".format(
                temperature_dht22, humidity_dht22))
        else:
            logger.warning("Failed to retrieve data from DHT22 sensor")
            logger.info("-" * 50)
            continue


        delta = CYCLE_SLEEP - (time.time() - t1)
        logger.debug("Sleeping for {:.4f} seconds".format(delta))
        if delta > 0:
            time.sleep(delta)
        sense.clear()

        logger.info("-" * 50)
        # Display on the Sense Hat
        dn.show_number(round(temp), 50, 0, 0)
        sleep(CYCLE_SLEEP)
        dn.show_number(round(hum), 50, 0, 50)
        sleep(CYCLE_SLEEP)
        dn.show_number(
            round(temperature_dht22), 0, 50, 0)
        sleep(CYCLE_SLEEP)


if __name__ == "__main__":
    main()
