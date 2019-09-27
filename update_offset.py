#!/usr/bin/env python3
import subprocess
import time
import datetime
import re

if __name__ == "__main__":
    error_count = 0
    while True:
        try:
            print(datetime.datetime.now())
            with open("/tmp/current_temperature.txt") as f:
                line = f.readlines()[0]
                sensor_temp = float(line)
            print("DHT22 Sensor reports:", sensor_temp)

            print("Reading from cometblue...")
            result = subprocess.run(
                ['cometblue device -p 1762 80:30:DC:E9:4E:50 get temperatures'], stdout=subprocess.PIPE, shell=True)
            result = result.stdout.decode("utf-8")
            # Extract current temp from result
            pattern = re.compile(r"Current temperature: ([0-9\.]+)")
            search_results = pattern.search(result)
            cometblue_temp = float(search_results.group(1))
            print("Cometblue reports:", cometblue_temp)

            correct_offset = sensor_temp - cometblue_temp
            print("Correct offset is:", round(correct_offset, 2))

            print("Setting correct offset...")
            result = subprocess.run(['cometblue device -p 1762 80:30:DC:E9:4E:50 set temperatures --temp-offset {}'.format(
                round(correct_offset))], stdout=subprocess.PIPE, shell=True)
            assert result.returncode == 0
            SLEEP_MINUTES = 30
            print("Sleeping for {} minutes".format(SLEEP_MINUTES))
            time.sleep(SLEEP_MINUTES* 60)

            # Reset error count
            error_count = 0

        except Exception as e:
            error_count += 1
            if error_count > 5:
                time.sleep(SLEEP_MINUTES * 60)
            print("Exception: {}".format(e))
            print("Retrying...")
        finally:
            print()
