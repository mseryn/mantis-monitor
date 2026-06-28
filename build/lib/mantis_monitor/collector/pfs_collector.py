
# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is

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

"""
This file contains the implementation of the \proc filesystem "PFS" Collector.

Here, process-based monitoring is completed using psutil, a python package
leveraging information from the PFS.

The PFS Collector is an example of one not requiring major setup - each 
TestRun() is made on-demand and really only exists to uniformly separate concerns
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



class PFSCollector(Collector):
    """
    This is the implementation of the proc filesystem data collector

    It inherits directly from the Collector() class.

    :ivar name: PFSCollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar data: Data from this Collector instance stored in the UDF
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar timescale: The time between collections in MS, comes from Configuration()
    """

    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        """
        Init the object

        :param configuration: Configuration object from this mantis-monitor instance
        :type configuration: Configuration()
        :param iteration: The current experimental iteration
        :type iteration: int
        :param benchmark: Benchmark class this Collector is initiated against
        :type benchmark: Benchmark()
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :type benchmark_set: str

        :return: None
        """

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
        """
        Collects all "Utilization" metrics from the psutil python package, which wraps calls 
        to the proc filesystem

        Explaining a design decision:

        Despite only using a single TestRun object, they are used here for several reasons.

        First, psutil has many "modes" of collection, which return different metrics.
        Currently, only "Utilization" is used.
        More are likely to be needed.

        Second, this TestRun() object is specifically designed to handle psutil over time.
        This is not the only way to leverage psutil, so non-time-dependent TestRuns are 
        likely to be designed with majorly different implementations.

        Third, these plausable extensions are easily handled with encapsulation, and
        the way this codebase approaches this is through TestRun objects.

        :return: None, yielded for each invocation of the Benchmark associated
        with this Collector instance

        """

        self.benchmark.before_each()

        data = await (PFSTimeTestRun("Utilization", self.benchmark, self.filename, self.iteration, self.timescale, \
            "unknown", self.benchmark_set).run())

        self.data.append(data)

        self.benchmark.after_each()
        yield

class PFSTimeTestRun():
    """
    Encapsulates a time-dependent call to psutil collecting the given category
    (ex, "Utilization").

    :ivar name: This PFSTimeTestRun()'s collection category
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar data: The data collected during this instance of Perf
    :ivar duration: The duration which this instance of Perf ran for
    :ivar measurements: The collected values through psutil
    :ivar units: The units of measurements


    The format of stored data is as follows (in a dictionary):
    - "benchmark_name": self.benchmark.name,
    - "benchmark_set":  self.benchmark_set,
    - "collector_name": self.name,
    - "iteration":      self.iteration,
    - "timescale":      self.timescale,
    - "units":          "count per timescale milliseconds",
    - "measurements":   list of strings,
    - "duration":       0,

    """
    def __init__(self, name, benchmark, filename, iteration, timescale, units, benchmark_set):
        """
        Init this PFSTimeTestRun()

        :param name: The collection set to call (psutil input)
        :param counters: A list of perf counters to run, length is <= pmu_count
        :param timescale: The time between collections in MS, comes from Configuration()
        :param filename: A unique filename to use for intermediate data storage
        :param benchmark: Benchmark class this Collector is initiated against
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :param iteration: The statistical or experimental iteration

        :return: None
        """

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
                        "duration":         0,
                        }

    async def run(self):
        """
        Call this to run this PFS monitoring instance using psutil
        """

        cpu_count = psutil.cpu_count()

        # Run benchmark
        starttime = time.time()

        print(self.benchmark.env)

        process = await asyncio.create_subprocess_shell(self.benchmark.get_run_command(), cwd=self.benchmark.cwd, env=self.benchmark.env)
        # process = subprocess.Popen(self.benchmark.get_run_command(), shell=True, executable="/bin/bash", cwd=self.benchmark.cwd, env=self.benchmark.env)

        await asyncio.sleep(0.1) # Let the shell start up

        shell_proc = psutil.Process(process.pid)
        children = shell_proc.children()
        
        for child in shell_proc.children(True):
            child.cpu_percent() # Returns dummy 0.0 value for the first call
        old_net_counters = psutil.net_io_counters(nowrap=True)._asdict()

        await asyncio.sleep(1)
        while (shell_proc.is_running()):
            timestamp = time.time() - starttime
            measurement = {}
            measurement_sets = ['memory_info', 'cpu_percent', 'io_counters']
            for child in shell_proc.children(True):
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
