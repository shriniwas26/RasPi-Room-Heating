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
import threading

CYCLE_SLEEP = 1
INTENSITY = 50

# DHT Sensor Config
DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = 4
temperature_dht22 = 0
temperature_sense = 0
humidity_dht22 = 0
humidity_sense = 0
pressure = 0


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


def measure():
    global temperature_dht22
    global temperature_sense
    global humidity_dht22
    global humidity_sense
    global pressure
    logger = logging.getLogger()
    sense = SenseHat()
    """ Read from the DHT22 sensor """
    while True:
        logger.info("Taking measurements")
        humidity_dht22, temperature_dht22 = Adafruit_DHT.read_retry(
            DHT_SENSOR, DHT_PIN)
        humidity_sense = sense.get_humidity()
        temperature_sense = sense.get_temperature()
        pressure = sense.get_pressure()

        logger.info("[DHT22]    Temperature = {:0.1f} C".format(
            temperature_dht22))
        logger.info("[DHT22]    Humidity = {:0.1f} %".format(
            humidity_dht22))

        logger.info("[SenseHat] Temperature = {:.1f} C".format(
            temperature_sense))
        logger.info("[SenseHat] Humidity = {:.1f} %".format(humidity_sense))
        logger.info("[SenseHat] Pressure = {:.1f} millibar".format(pressure))

        # Write date to temp files (for use by other programs)
        with open("/tmp/dht22_reading.txt", "w") as fh:
            fh.write("{:.2f}\n{:.2f}\n".format(
                temperature_dht22, humidity_dht22))
        with open("/tmp/temperature_sense_hat.txt", "w") as fh:
            fh.write("{}\n".format(temperature_sense))
        time.sleep(15)


def display_square(x_offset):
    square_shape = [(x, y) for x in range(2) for y in range(2)]
    sense = SenseHat()
    for x, y in square_shape:
        assert x + x_offset < 8
        sense.set_pixel(x + x_offset, y, INTENSITY, INTENSITY, INTENSITY)


def main():
    logger = setup_logger()
    sense = SenseHat()
    sense.set_rotation(270)
    sense.clear()
    number_display = sense_hat_display_number.NumberDisplay(rotation=270)
    color_temp = [INTENSITY, 0, 0]
    color_hum = [0, INTENSITY, 0]
    color_pre = [0, 0, INTENSITY]
    measure_thread = threading.Thread(target=measure)
    measure_thread.start()
    while True:
        if not measure_thread.isAlive():
            logger.error("Measurement thread crashed!")
            os._exit(1)

        # Display Sense-Hat Temperature/Humidit
        sense.clear()
        display_square(x_offset=0)

        number_display.show_number(round(temperature_sense), *color_temp)
        time.sleep(CYCLE_SLEEP)

        number_display.show_number(round(humidity_sense), *color_hum)
        time.sleep(CYCLE_SLEEP)

        number_display.show_number(round(pressure) % 100, *color_pre)
        time.sleep(CYCLE_SLEEP)

        # Display DHT22 Temperature/Humidity
        sense.clear()
        display_square(x_offset=0)

        number_display.show_number(round(temperature_dht22), *color_temp)
        time.sleep(CYCLE_SLEEP)

        sense.clear()
        number_display.show_number(round(humidity_dht22), *color_hum)
        time.sleep(CYCLE_SLEEP)


if __name__ == "__main__":
    main()
