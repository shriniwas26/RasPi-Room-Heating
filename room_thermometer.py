#!/usr/bin/env python3
import time
import logging
import logging.handlers
import os
import time
import threading
from datetime import datetime as dt
APP_DEBUG = False


class Thermometer(object):
    def __init__(self):
        self.CYCLE_SLEEP = 1
        self.SENSING_DELAY = 15
        self.INTENSITY = 50
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
            dirname + "/logs/room_weather.log", when='midnight', backupCount=1000)
        fh_info.setLevel(logging.INFO)
        fh_info.setFormatter(formatter)
        self.logger.addHandler(fh_info)

        # Setup console handler
        ch = logging.StreamHandler()
        if APP_DEBUG:
            ch.setLevel(logging.DEBUG)
        else:
            ch.setLevel(logging.ERROR)

        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

    def measure_sense_hat(self):
        from sense_hat import SenseHat

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
                with open("/tmp/sense_hat_reading.txt", "w") as fh:
                    fh.write("{}\n".format(self.temperature_sense))
            time.sleep(self.SENSING_DELAY)

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
                self.logger.info("[DHT22] Temperature = {:0.1f} C".format(
                    self.temperature_dht22))
                self.logger.info("[DHT22] Humidity = {:0.1f} %".format(
                    self.humidity_dht22))
                # Write date to temp files (for use by other programs)
                with open("/tmp/dht22_reading.txt", "w") as fh:
                    fh.write("{:.2f}\n{:.2f}\n".format(
                        self.temperature_dht22, self.humidity_dht22))
            time.sleep(self.SENSING_DELAY)

    def display_sense_hat(self):
        from sense_hat import SenseHat
        import sense_hat_display_number

        sense = SenseHat()
        sense.set_rotation(270)
        sense.clear()
        number_display = sense_hat_display_number.NumberDisplay(rotation=270)
        def display_square(x_offset):
            square_shape = [(x, y) for x in range(2) for y in range(2)]
            for x, y in square_shape:
                assert x + x_offset < 8
                sense.set_pixel(x + x_offset, y,
                                self.INTENSITY, self.INTENSITY, self.INTENSITY)

        while True:
            time_now = dt.now()
            if time_now.hour <= 6:
                self.INTENSITY = 0
            else:
                self.INTENSITY = 50

            color_temp = [self.INTENSITY, 0, 0]
            color_hum = [0, self.INTENSITY, 0]
            color_pre = [0, 0, self.INTENSITY]

            # Display Sense-Hat Temperature/Humidit
            sense.clear()
            display_square(x_offset=0)

            number_display.show_number(
                round(self.temperature_sense), *color_temp)
            time.sleep(self.CYCLE_SLEEP)

            number_display.show_number(round(self.humidity_sense), *color_hum)
            time.sleep(self.CYCLE_SLEEP)

            number_display.show_number(round(self.pressure) % 100, *color_pre)
            time.sleep(self.CYCLE_SLEEP)

            # Display DHT22 Temperature/Humidity
            sense.clear()
            display_square(x_offset=6)

            number_display.show_number(
                round(self.temperature_dht22), *color_temp)
            time.sleep(self.CYCLE_SLEEP)

            number_display.show_number(
                round(self.humidity_dht22), *color_hum)
            time.sleep(self.CYCLE_SLEEP)

    def display_grove_lcd(self):
        import grove_rgb_lcd as grl
        grl.setRGB(r=0, g=0, b=127)
        grl.setText("")
        while True:
            animation_chars = ['_', '|']
            for i in range(len(animation_chars)):
                s1 = "Tmp = {:.1f} C {}".format(self.temperature_dht22, animation_chars[i])
                s2 = "Hum = {:.1f} %".format(self.humidity_dht22)
                assert len(s1) <= 16
                assert len(s2) <= 16
                grl.setText_norefresh(s1 + "\n" + s2)
                time.sleep(0.5)

    def main(self):
        app_functions = [
            self.measure_dht22,
            self.display_grove_lcd
        ]
        # app_functions = [
        #     self.measure_dht22,
        #     self.measure_sense_hat,
        #     self.display_sense_hat
        # ]

        app_threads = [threading.Thread(target=f) for f in app_functions]
        for t in app_threads:
            t.start()

        while True:
            time.sleep(1)
            all_running = True
            for t in app_threads:
                if not t.is_alive():
                    self.logger.error("Thread {} crashed".format(t.getName))
                    all_running = False

            if not all_running:
                self.logger.error("One or more threds crashed")
                os._exit(1)


if __name__ == "__main__":
    t = Thermometer()
    t.main()
