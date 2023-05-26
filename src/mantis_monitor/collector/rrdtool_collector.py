# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is
# copyright (C) 2016-2023 by Melanie Cornelius.

# Mantis is free software:
# you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# Mantis is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with Mantis. If not, see <https://www.gnu.org/licenses/>.


#import logging
import math
import subprocess
import os
import os.path
import csv
import copy
import datetime
import psutil

import pprint
import pandas

from mantis_monitor.collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class RRDToolCollector(Collector):
    """
    This is the implementation of the rrdtool data collector
    """

    def __init__(self, configuration, iteration, benchmark):
        self.name = "RRDToolCollector"
        self.description = "Collector for configuring rrdtool data collection"
        self.benchmark = benchmark
        self.iteration = iteration

        self.measurements = configuration.collector_modes["rrdtool"]

        # set up units - better way?
        units = {"default":             "unknown",
                 "power":     "(time, W)",
                }

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-utilization".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)
        self.data = []


    def run_all(self):
        self.benchmark.before_each()

        self.data.append(PFSTimeTestRun("Utilization", self.benchmark, self.filename, self.iteration, self.timescale, \
            self.measurements, "unknown").run())

        self.benchmark.after_each()

class RRDToolTestRun():
    """
    This is the generic RRDTool testrun to collect utilization measurements over time
    """
    def __init__(self, name, benchmark, filename, iteration, timescale, measurements, units):
        self.name = name
        self.benchmark = benchmark
        self.filename = filename
        self.iteration = iteration
        self.timescale = timescale
        self.measurements = measurements
        self.units = units

        measurements_string = ",".join(self.measurements)
        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "units":            self.units, \
                        "measurements":     self.measurements, \
                        }

    def run(self):
        # Run it

        cpu_count = psutil.cpu_count()
        cpu_vals = {}
        mem_vals = []

        # Run benchmark
        starttime = datetime.datetime.now()

        process = subprocess.Popen(self.benchmark.get_run_command(), shell=True, executable="/bin/bash", cwd=self.benchmark.cwd, env=self.benchmark.env)

        # TODO: probably don't spin-loop here!
        while (process.poll() is None):
            time = datetime.datetime.now()
            cpu_val = psutil.cpu_percent(interval=None, percpu=True)
            cpu_vals[time] = cpu_val
            mem_val = psutil.virtual_memory().used
            mem_vals.append((time, mem_val))

        endtime = datetime.datetime.now()

        # Collect data
        if "memory_utilization" in self.measurements:
            self.data["memory_utilization"] = mem_vals

        if "cpu_utilization" in self.measurements:
            # TODO: don't do this
            for i in range(0, cpu_count):
                column = "cpu_{index}_utilization".format(index = i)
                parsed_data = [[x, y[i]] for x, y in cpu_vals.items()]
                self.data[column] = parsed_data

        self.data["duration"] = (endtime - starttime).total_seconds()

        return self.data

Collector.register_collector("rrdtool", RRDToolCollector)
