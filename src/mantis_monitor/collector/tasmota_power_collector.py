"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016-2023 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""

#import logging
import math
import asyncio
import os
import os.path
import csv
import copy
import time
import psutil

import pprint
import pandas
import numbers
import paho.mqtt.client as mqtt
import json

from mantis_monitor.collector.collector import Collector

class TasmotaPowerCollector(Collector):
    """
    This is the implementation of the tasmota power data collector
    """

    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        self.name = "TasmotaPower"
        self.description = "Collector for collecting power from Tasmota smart plugs"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.mqtt = configuration.collector_modes["TasmotaPower"]["mqtt"]

        # set up units - better way?
        units = {"default":             "unknown",
                 "power_utilization":   "(power, watts)"
                }

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-set_{benchsetstring}-power".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name, benchsetstring = self.benchmark_set)
        self.data = []


    async def run_all(self):
        self.benchmark.before_each()

        data = await (TasmotaPowerTestRun("TasmotaPower", self.benchmark, self.filename, self.iteration, self.timescale, \
            "unknown", self.benchmark_set, self.mqtt).run())

        self.data.append(data)

        self.benchmark.after_each()
        yield

class TasmotaPowerTestRun():
    """
    This is the generic Proc FS testrun to collect utilization measurements over time
    """
    def __init__(self, name, benchmark, filename, iteration, timescale, units, benchmark_set, mqtt):
        self.name = name
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.filename = filename
        self.iteration = iteration
        self.timescale = timescale
        self.units = units
        self.measurements = []
        self.mqtt = mqtt

        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "benchmark_set":    self.benchmark_set, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "measurements":     [], \
                        "units":            self.units, \
                        }
    def record_data(self, client, userdata, msg):
        message = json.loads(msg.payload)["StatusSNS"]
        measurement = {}
        measurement["time"] = time.time() - self.starttime
        measurement["power"] = message['ENERGY']['Power']
        measurement["apparent_power"] = message["ENERGY"]['ApparentPower']
        measurement["reactive_power"] = message["ENERGY"]['ReactivePower']
        self.measurements.append(measurement)


    async def run(self):
        # Connect to MQTT

        client = mqtt.Client(clean_session=True)
        client.on_message = self.record_data
        client.username_pw_set(self.mqtt["username"], self.mqtt["password"])
        client.connect(self.mqtt["host"])
        client.loop_start()
        client.subscribe('stat/' + self.mqtt["topic"] + '/STATUS10')
        # Run it

        # Run benchmark
        self.starttime = time.time()

        process = await asyncio.create_subprocess_shell(self.benchmark.get_run_command(), cwd=self.benchmark.cwd, env=self.benchmark.env)
        # process = subprocess.Popen(self.benchmark.get_run_command(), shell=True, executable="/bin/bash", cwd=self.benchmark.cwd, env=self.benchmark.env)

        await asyncio.sleep(0.1) # Let the shell start up

        shell_proc = psutil.Process(process.pid)
        children = shell_proc.children(True)
        
        for child in children:
            child.cpu_percent() # Returns dummy 0.0 value for the first call
        old_net_counters = psutil.net_io_counters(nowrap=True)._asdict()

        await asyncio.sleep(1)
        while (shell_proc.is_running()):
            client.publish('cmnd/' + self.mqtt["topic"] + '/Status', "10")
            await asyncio.sleep(1)

        self.data["duration"] = time.time() - self.starttime
        client.disconnect()
        client.loop_stop()

        # pivot measurement format
        for row in self.measurements:
            for key in row.keys():
                if key == "time":
                    continue
                if key not in self.data:
                    self.data[key] = []
                    self.data["measurements"].append(key)
                self.data[key].append([row["time"], row[key]])

        return self.data

Collector.register_collector("TasmotaPower", TasmotaPowerCollector)
