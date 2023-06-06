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

"""
This file contains the implementation of the time-to-completion (TTC) Collector.

All this Collector does is run the program with no additional monitoring
and time how long the entire command takes to complete.

Since and while a fully-fledged tutorial for creating new Collectors doesn't
exist, the PerfCollector() is a good example implementation off which new
Collectors could be based.


.. note::

   For each newly-created Collector(), register_collector() must be called,
   and the file must be added to __init__.py
"""



#import logging
import math
import subprocess
import asyncio
import os
import datetime

import pprint

from mantis_monitor.collector.collector import Collector

class TTCCollector(Collector):
    """
    This is the implementation of the ttc data collector

    It inherits directly from the Collector() class.


    :ivar name: TTCCollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar configuration: Configuration object from this mantis-monitor instance
    :ivar testruns: List of TestRun() instances to run against this Collector

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

        self.name = "TTCCollector"
        self.description = "Collector for baseline ttc collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.testruns = []
        self.data = []

        self.testruns.append(TTCTestRun(self.name, self.benchmark, self.iteration, self.benchmark_set))

    async def run_all(self):
        """
        Runs all TTCTestRun() instances for this Benchmark()

        :return: None, yielded for each invocation of the Benchmark associated
        with this Collector instance

        """
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            self.data.append(data)
            yield


class TTCTestRun():
    """
    Encapsulates the call to run the benchmark and collect the total runtime

    :ivar name: "TTCCollector"
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar data: The data collected during this instance of Perf
    :ivar duration: The duration which this instance of Perf ran for

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
    def __init__(self, name, benchmark, iteration, benchmark_set):
        """
        Init this TTCTestRun()

        :param name: TTCCollector
        :param benchmark: Benchmark class this Collector is initiated against
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :param iteration: The statistical or experimental iteration

        :return: None
        """

        self.name = name
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.runcommand = self.benchmark.get_run_command()
        self.data = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "units":          "seconds",
            "measurements":   "baseline_duration",
            "duration":       0,
        }

        self.duration = None

    async def run(self):
        """
        Call this to run this instance of the associated Benchmark() and collect
        its runtime
        """

        starttime = datetime.datetime.now()
        process = await asyncio.create_subprocess_shell(self.runcommand, cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()
        # process = subprocess.run(self.runcommand, shell=True, cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()

        if process.returncode != 0:
            print('Oops, bad data...')
            return self.data

        self.data["duration"] = (endtime - starttime).total_seconds()

        return self.data


Collector.register_collector("ttc", TTCCollector)
