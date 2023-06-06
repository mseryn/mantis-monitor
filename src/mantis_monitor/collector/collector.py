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
In mantis-monitor, Collectors are objects implementing different monitoring
and profiling tools.

Natively-supported Collectors include:
    - Perf
    - /proc filesystem
    - Time-to-completion
    - NVIDIA smi
    - NVIDIA nvprof
    - NVIDIA ncu
    - RRDtool

Each collector instance is initialized against a benchmark, a co-running set,
and an experimental iteration. Benchmarks are unaware of what collectors
are running against them, so entanglement is one-way.

To implement a new Collector, inherit from the Collector() class, and
overwrite functions as needed.

The Perf Collector is a good example of a fully-fledged implementation
on the "perf stat" monitoring tool.

Until a fully-fledged tutorial is created, please refer to perf_collector.py
for an example implementation.
"""

import logging
import math
import subprocess
import os

import pprint

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Collector():
    """
    This is the generic form for a collector; use as an interface

    :cvar implementations: List of all registered Collector classes
    :type implementations: list

    :ivar name: initial value: ""
    :type name: str
    :ivar description: initial value: ""
    :type descriotion: str
    :ivar benchmark: Benchmark class this Collector is initiated against
    :type benchmark: Benchmark()
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :type benchmark_set: str
    :ivar iteration: The statistical or experimental iteration
    :type iteration: int
    :ivar configuration: Configuration object from this mantis-monitor instance
    :type configuration: Configuration()
    :ivar testruns: List of TestRun() instances to run against this Collector
    :type testruns: TestRun()
    :ivar data: Data from this Collector instance stored in the UDF
    """
    implementations = {}

    @staticmethod
    def register_collector(name, collector_class):
        """
        Register a new collector class

        Call this at the end of your new_collector.py file

        :param name: New name for the collector
        :type name: str
        :param formatter_class: Collector class made for registration
        :type formatter_class: Collector()
        """

        if name in Collector.implementations:
            logging.error("A collector named {} was supplied to be registered, but a collector by that name already exists".format(name))
            raise ValueError("Collector name collision")
        Collector.implementations[name] = collector_class

    @staticmethod
    def get_collector(name, configuration, iteration, benchmark, benchmark_set):
        """
        Using the string name of a Collector implementation, return the object

        :param name: Name of the Collector to return
        :type name: str

        :return: Collector.implementations[name]()
        :rtype: Collector()
        """

        if name not in Collector.implementations:
            logging.error("A collector named {} was requested, but no collector by that name exists (is the configuration correct?)".format(name))
            return None
        return Collector.implementations[name](configuration, iteration, benchmark, benchmark_set)



    def __init__(self, configuration, iteration, benchmark, benchmark_set = "solo"):
        """
        Init the object
        Run setup

        Sets generic initial values for name and description
        Stores information on the benchmark this collector is initialized against

        Feel free to implement additional attributes as-needed

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

        self.name = ""
        self.description = ""
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.configuration = configuration
        self.testruns = []
        self.data = None

        self.setup()

    def setup(self):
        """
        Performs any needed work to fully initialize the object
        
        Usually, this is where TestRun() objects will be created and added to the
        Collector's list

        Some Collectors won't need any setup, in which case, this function (and
        its call in __init__) can be ignored.

        :return: None
        """
        pass

    async def run_all(self):
        """
        Runs all collection involved in this Collector instance

        Handles running the Collector's Benchmark's per-run setup and teardown

        Yields results as it goes

        Recommended functionality involves:
        - For each TestRun
        - Run the associated Benchmark's Benchmark.before_each()
        - Await the results of one TestRun
        - Collect the data
        - Run the associated Benchmark's Benchmark.after_each()
        - Add the collected data to this Collector instance's data
        - Yield

        As an example, please see the run_all() implementation on PerfCollector()

        :return: None, yielded for each invocation of the Benchmark associated
        with this Collector instance
        """
        yield None

# TODO make interface for testrun?
