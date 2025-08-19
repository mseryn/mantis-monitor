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
This file contains the implementation of the AMD-SMI Collector.

The AMD SMI Collector can use:
- amd-smi

This Collector is a good example of leveraging different TestRun()
implementations to achieve different monitoring tasks.
"""

#import logging
import math
import subprocess
import asyncio
import os
import os.path
import csv
import copy
import datetime

import pprint
import pandas

from mantis_monitor.collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class AmdSMICollector(Collector):
    """
    This is the implementation of the base AMDSMI Collector.

    It inherits directly from the Collector() class.

    :ivar name: AmdSMICollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar configuration: Configuration object from this mantis-monitor instance
    :ivar testruns: List of TestRun() instances to run against this Collector
    :ivar data: Data from this Collector instance stored in the UDF

    :ivar modes: Which metrics to collect, comes from Configuration()
    :ivar gen: The SM value on the system, comes from Configuration()
    :ivar global_id: An int used to uniquely identify each TestRun()
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    """
    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        """
        Init the object
        Run setup

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
        self.name = "AmdSMICollector"
        self.description = "Collector for configuring nvidia profiling metric collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-set_{benchsetstring}-nvidia_{{nvidia_identifier}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name, benchsetstring = self.benchmark_set)
        self.data = []
        self.global_ID = 0

        self.setup()


    def setup(self):
        """
        Sets up all SMIOverTimeTestRun() and NsysTestRun() instances to collect 
        all counters and metrics

        Attempts to abstract away from the user what values are needed

        TODO:
        - Extend backward to use rocm-smi if amdsmi not available based on SM version
        - Overlap modes that can co-collect
        - Embrace the NVP datatype

        :return: None
        """

        self.testruns.append(AmdSMIOverTimeTestRun("AmdSMIOverTime", self.benchmark, self.iteration, self.timescale, ["power_usage", "hotspot_temperature", "memory_temperature", "gfx", "gfx_clock", "mem", "mem_clock", "encoder", "decoder", "vclock", "dclock", "vram_used", "vram_total", "pcie_bw"], "time, unknown", self.benchmark_set))

    async def run_all(self):
        """
        Runs all TestRun() instances for this Benchmark()

        :return: None, yielded for each invocation of the Benchmark associated
        with this Collector instance
        """
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            if isinstance(data, list):
                self.data.extend(data)
            else:
                self.data.append(data)
            yield

class AmdSMIOverTimeTestRun():
    """
    Encapsulates each individual call to amd-smi over time

    :ivar name: This TestRun()'s unique name (using global_id)
    :ivar measurements: The list of metrics to collect
    :ivar units: The units of the measurements
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar data: The data collected during this instance of amd-smi
    :ivar duration: The duration which this instance of amd-smi ran for

    The format of stored data is as follows (in a dictionary):
    - "benchmark_name": self.benchmark.name,
    - "benchmark_set":  self.benchmark_set,
    - "collector_name": self.name,
    - "iteration":      self.iteration,
    - "timescale":      self.timescale,
    - "units":          "count per timescale milliseconds",
    - "measurements":   self.counters,
    - "duration":       0,
    """
    def __init__(self, name, benchmark, iteration, timescale, measurements, units, benchmark_set):
        """
        Init this TestRun()

        :param name: This TestRun()'s unique name (using global_id)
        :param measurements: The list of metrics to collect
        :param units: The units of the measurements
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
        self.iteration = iteration
        self.timescale = timescale
        self.measurements = measurements
        self.units = units
        self.duration = 0
        watchTime = int(self.timescale / 1000)

        self.smi_runstring = f"amd-smi monitor -w{watchTime} --csv --gfx --mem --encoder --decoder --temperature --power-usage --pcie -v --file /tmp/amdsmi-out.csv"
        self.smi_runcommand = self.smi_runstring
        self.bench_runcommand = self.benchmark.get_run_command()
        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "benchmark_set":    self.benchmark_set, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "units":            self.units, \
                        "measurements":     self.measurements, \
                        "duration":         self.duration, \
                        }

    # TODO (zcornelius): Fix SMI to use as a process wrapper here, instead of system-wide
    async def run(self):
        """
        Call this to run this instance of NVIDIA SMI
        """

        # Run it

        # Start SMI
        smi_filename = "/tmp/amdsmi-out.csv"
        smi_proc = subprocess.Popen(self.smi_runcommand.split(" "))

        # Run benchmark
        print('Running command ' + self.bench_runcommand)
        starttime = datetime.datetime.now()
        process = await asyncio.create_subprocess_shell(self.bench_runcommand, cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()
        # Old subprocess mechanism
        # process = subprocess.run(self.bench_runcommand, shell=True, executable="/bin/bash", cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()

        # Kill SMI
        smi_proc.kill()

        # Collect data
        with open("/tmp/amdsmi-out.csv", 'r') as csvfile:
            dr = csv.DictReader(csvfile)
            start_time = None
            for row in dr:
                if start_time is None:
                    start_time = int(row["timestamp"])
                time = int(row["timestamp"]) - start_time
                gpu_index = row["gpu"]
                for measurement, value in row.items():
                    if measurement in self.measurements and value != "N/A":
                        key = "gpu_{index}_{measurement}".format(index = gpu_index, measurement = measurement)
                        self.data.setdefault(key, []).append([time, float(value.strip())])

        # Clean up files
        os.remove(smi_filename)

        self.duration = (endtime - starttime).total_seconds()
        self.data["duration"] = self.duration

        return self.data


Collector.register_collector("amdsmi", AmdSMICollector)
