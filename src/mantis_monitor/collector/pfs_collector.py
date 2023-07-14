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

from mantis_monitor.collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

def selectProcessByPid(array, default, pid):
    for child in array:
        if child.pid == pid:
            return child
    return default

class PFSCollector(Collector):
    """
    This is the implementation of the proc filesystem data collector
    """

    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        self.name = "PFSCollector"
        self.description = "Collector for configuring proc filesystem metric collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration

        # set up units - better way?
        units = {"default":             "unknown",
                 "cpu_utilization":     "(time, pct)",
                 "memory_utilization":  "(time, pct)",
                }

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-set_{benchsetstring}-utilization".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name, benchsetstring = self.benchmark_set)
        self.data = []


    async def run_all(self):
        self.benchmark.before_each()

        data = await (PFSTimeTestRun("Utilization", self.benchmark, self.filename, self.iteration, self.timescale, \
            "unknown", self.benchmark_set).run())

        self.data.append(data)

        self.benchmark.after_each()
        yield

class PFSTimeTestRun():
    """
    This is the generic Proc FS testrun to collect utilization measurements over time
    """
    def __init__(self, name, benchmark, filename, iteration, timescale, units, benchmark_set):
        self.name = name
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.filename = filename
        self.iteration = iteration
        self.timescale = timescale
        self.units = units
        self.measurements = []

        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "benchmark_set":    self.benchmark_set, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "measurements":     [], \
                        "units":            self.units, \
                        }

    async def run(self):
        # Run it

        cpu_count = psutil.cpu_count()

        # Run benchmark
        starttime = time.time()

        print(self.benchmark.env)

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
            timestamp = time.time() - starttime
            measurement = {}
            measurement_sets = ['memory_info', 'cpu_percent', 'io_counters']
            new_children = shell_proc.children(True)
            children = [ selectProcessByPid(children, child, child.pid) for child in new_children ]
            for child in children:
                try:
                    child_measurements = child.as_dict(measurement_sets)
                except psutil.NoSuchProcess as e:
                    continue
                for mset in measurement_sets:
                    # Convert scalar values to dict values
                    if (isinstance(child_measurements[mset], numbers.Number)):
                        if mset not in measurement:
                            measurement[mset] = 0
                        measurement[mset] += child_measurements[mset]
                    else:
                        for key, value in child_measurements[mset]._asdict().items():
                            if key not in measurement:
                                measurement[key] = 0
                            measurement[key] += value
            # Process network counters
            # These are absolute values, so compare against the last reading
            net_counters = psutil.net_io_counters(nowrap=True)._asdict()
            for key, value in net_counters.items():
                measurement[key] = value - old_net_counters[key]
            old_net_counters = net_counters

            measurement["time"] = timestamp
            self.measurements.append(measurement)
            await asyncio.sleep(1)

        self.data["duration"] = time.time() - starttime

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

Collector.register_collector("utilization", PFSCollector)
