#!/usr/bin/env python3
from sense_hat import SenseHat
import time
import sense_hat_display_number
import logging
import logging.handlers
import os
import datetime
import time
import threading

CYCLE_SLEEP = 1
SENSING_DELAY = 15
INTENSITY = 50


class Thermometer(object):
    def __init__(self):
        self.temperature_dht22 = 0
        self.temperature_sense = 0
        self.humidity_dht22 = 0
        self.humidity_sense = 0
        self.pressure = 0
        self.sensor_lock = threading.Lock()
        self.setup_logger()

    def setup_logger(self):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)

        # Define format
        formatter = logging.Formatter('%(asctime)s %(message)s')
        formatter.default_msec_format = '%s.%03d'

        # Setup file handler
        dirname, _filename = os.path.split(os.path.abspath(__file__))
        fh_info = logging.handlers.TimedRotatingFileHandler(
            dirname + "/logs/room_weather.log", when='midnight', backupCount=50)
        fh_info.setLevel(logging.INFO)
        fh_info.setFormatter(formatter)
        self.logger.addHandler(fh_info)

        # Setup ch
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def measure_sense_hat(self):
        sense = SenseHat()
        while True:
            with self.sensor_lock:
                self.logger.info("Taking measurements from Sense Hat")
                self.humidity_sense = sense.get_humidity()
                self.temperature_sense = sense.get_temperature()
                self.pressure = sense.get_pressure()
                self.logger.info("[SenseHat] Temperature = {:.1f} C".format(
                    self.temperature_sense))
                self.logger.info(
                    "[SenseHat] Humidity = {:.1f} %".format(self.humidity_sense))
                self.logger.info(
                    "[SenseHat] Pressure = {:.1f} millibar".format(self.pressure))
                # Write date to temp files (for use by other programs)
                with open("/tmp/temperature_sense_hat.txt", "w") as fh:
                    fh.write("{}\n".format(self.temperature_sense))
            time.sleep(SENSING_DELAY)

    def measure_dht22(self):
        import Adafruit_DHT
        # DHT Sensor Config
        DHT_SENSOR = Adafruit_DHT.DHT22
        DHT_PIN = 4
        while True:
            with self.sensor_lock:
                self.logger.info("Taking measurements from DHT22")
                self.humidity_dht22, self.temperature_dht22 = Adafruit_DHT.read_retry(
                    DHT_SENSOR, DHT_PIN)
                self.logger.info("[DHT22]    Temperature = {:0.1f} C".format(
                    self.temperature_dht22))
                self.logger.info("[DHT22]    Humidity = {:0.1f} %".format(
                    self.humidity_dht22))
                # Write date to temp files (for use by other programs)
                with open("/tmp/dht22_reading.txt", "w") as fh:
                    fh.write("{:.2f}\n{:.2f}\n".format(
                        self.temperature_dht22, self.humidity_dht22))
            time.sleep(SENSING_DELAY)

    def display_sense_hat(self):
        sense = SenseHat()
        sense.set_rotation(270)
        sense.clear()
        number_display = sense_hat_display_number.NumberDisplay(rotation=270)
        color_temp = [INTENSITY, 0, 0]
        color_hum = [0, INTENSITY, 0]
        color_pre = [0, 0, INTENSITY]

        def display_square(x_offset):
            square_shape = [(x, y) for x in range(2) for y in range(2)]
            for x, y in square_shape:
                assert x + x_offset < 8
                sense.set_pixel(x + x_offset, y,
                                INTENSITY, INTENSITY, INTENSITY)

        while True:
            # Display Sense-Hat Temperature/Humidit
            sense.clear()
            display_square(x_offset=0)

            number_display.show_number(
                round(self.temperature_sense), *color_temp)
            time.sleep(CYCLE_SLEEP)

            number_display.show_number(round(self.humidity_sense), *color_hum)
            time.sleep(CYCLE_SLEEP)

            number_display.show_number(round(self.pressure) % 100, *color_pre)
            time.sleep(CYCLE_SLEEP)

            # Display DHT22 Temperature/Humidity
            sense.clear()
            display_square(x_offset=6)

            number_display.show_number(
                round(self.temperature_dht22), *color_temp)
            time.sleep(CYCLE_SLEEP)

            number_display.show_number(
                round(self.humidity_dht22), *color_hum)
            time.sleep(CYCLE_SLEEP)

    def main(self):
        app_functions = [
            self.measure_dht22,
            self.measure_sense_hat,
            self.display_sense_hat
        ]
        app_threads = [threading.Thread(target=f) for f in app_functions]
        for t in app_threads:
            t.start()

        while True:
            time.sleep(1)
            for t in app_threads:
                if not t.is_alive():
                    self.logger.error("Thread {} crashed. Exiting".format(t.getName))
                    os._exit(1)

if __name__ == "__main__":
    t = Thermometer()
    t.main()
