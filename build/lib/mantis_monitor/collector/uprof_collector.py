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
This file contains the implementation of the AMD uProf Collector.
"""

import math
import subprocess
import asyncio
import os
import datetime

import pprint

from mantis_monitor.collector.collector import Collector

class uProfCollector(Collector):
    """
    This is the implementation of the AMD uProf data collector.

    It inherits directly from the Collector() class.


    :ivar name: uProfCollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar configuration: Configuration object from this mantis-monitor instance
    :ivar testruns: List of TestRun() instances to run against this Collector
    :ivar data: Data from this Collector instance stored in the UDF
    :ivar uprof_path: An optional path to uprof

    :ivar modes: A list of strings relating to different metrics to collect
    Currently supports:
    - collect

    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar global_id: An int used to uniquely identify each PerfTestRun()
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

        self.name = "uProfCollector"
        self.description = "Collector for configuring AMD uProf data collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-set_{benchsetstring}-uprof_{{uprof_identifier}}".format(testname = configuration.test_name, iter_count = iteration, benchstring = benchmark.name, benchsetstring = self.benchmark_set)

        if "path" in configuration.collector_modes["uprof"].keys():
            self.uprof_path = os.path.join(configuration.collector_modes["uprof"]["path"], "AMDuProfCLI")
        else:
            self.uprof_path = "AMDuProfCLI"

        self.modes = list(configuration.collector_modes["uprof"].keys())
        self.testruns = []

        self.data = []

        self.setup()

    def setup(self):
        """
        Sets up all uProfTestRun() instances to collect all counters and metrics

        :return: None
        """
        if len(self.modes) == 0 or "collect" in self.modes:
            current_filename = self.filename.format(uprof_identifier = "collect")
            self.testruns.append(uProfCollectTestRun("uProfCollect", configuration.collector_modes["uprof"]["collect"], 
                self.uprof_path, self.timescale, self.benchmark, 
                current_filename, self.iteration, self.benchmark_set))

    async def run_all(self):
        """
        Runs all uProfTestRun() instances for this Benchmark()

        :return: None, yielded for each invocation of the Benchmark associated
        with this Collector instance

        """
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            self.data.append(data)
            yield


# --- Begin test run for perf
class uProfCollectTestRun():
    """
    Encapsulates each call to the uProf collect tool in summary reporting mode

    Since uProf collect supports getting multiple config types at a time, only
    one SummaryTestRun is initiated

    :ivar name: This uProfTestRun()'s unique name
    :ivar uprof_path: The path to the system's uprof instillation, 
    defaults to running the command directly
    :ivar collect_modes: A list of collect options from the config.yaml
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration

    :ivar runstring: The command string for running Perf
    :ivar runcommand: The actual command to run (including Benchmark() entanglement)
    :ivar data: The data collected during this instance of Perf
    :ivar duration: The duration which this instance of Perf ran for

    The format of stored data is as follows (in a dictionary):
    - "benchmark_name": self.benchmark.name,
    - "benchmark_set":  self.benchmark_set,
    - "collector_name": self.name,
    - "iteration":      self.iteration,
    - "timescale":      self.timescale,
    - "units":          "summary"
    - "measurements":   self.collect_modes,
    - "duration":       0,
    """
    def __init__(self, name, uprof_collect_path, collect_modes, timescale, benchmark, filename, iteration, benchmark_set):
        """
        Init this PerfTestRun()

        :param name: This PerfTestRun()'s unique name (using global_id)
        :param uprof_path: The path to uprof on this system, defaults to running in the cwd
        :param collect_modes: The options to use for uprof collect
        :param timescale: The time between collections in MS, comes from Configuration()
        :param filename: A unique filename to use for intermediate data storage
        :param benchmark: Benchmark class this Collector is initiated against
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :param iteration: The statistical or experimental iteration

        :return: None
        """
        self.name = name
        self.uprof_path = uprof_path
        self.timescale = timescale
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.filename = filename
        self.iteration = iteration

        self.collect_modes = collect_modes

        self.runstring = "{uprof_path} collect --config {collect_list} -o {filename} {bench_runcommand}"
        self.runstring.format(self.filename, self.benchmark.get_run_command(),
            uprof_path = self.uprof_path,
            collect_list = ",".join(self.collect_modes))

        self.data = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "timescale":      self.timescale,
            "units":          "summary",
            "measurements":   ",".join(self.collect_modes),
            "duration":       0,
        }
        self.duration = None
        for counter in self.counters:
            self.data[counter] = []

    async def run(self):
        """
        Call this to run this instance of Perf

        This involves:
        - Creating a subprocess shell with the runcommand
        - Passing in any environment or working directory for the associated Benchmark()
        - Waiting for this subprocess to complete
        - Storing the runtime (duration)
        - Postprocessing the resulting data
        - Removing lingering files from collecting data
        """
        # Run it
        #logging.info("running following command:")
        #logging.info(self.runcommand)

        starttime = datetime.datetime.now()
        process = await asyncio.create_subprocess_shell(self.runcommand, cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()
        # process = subprocess.run(self.runcommand, shell=True, cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()

        if process.returncode != 0:
            #logging.error("Perf command failed with error:")
            # TODO: multiline log messages are theoretically bad practice
            #logging.error(process.stderr)
            #logging.error("Check that all configured counters are valid")
            # should we be louder about this?
            print('Oops, bad data...')
            #print(process.stderr)
            # is it really a good idea to just drop this?
            return self.data

        # Collect data
        with open(os.path.join((self.benchmark.cwd or ''), self.filename), 'r') as csvfile:
        #with open(self.filename, 'r') as csvfile:
            for line in csvfile:
                line = line.strip().split(",")
                if len(line) > 1 and "#" not in line[0]:
                    time = float(line[0])
                    measurement_name = line[3]
                    try:
                        measurement_value = float(line[1])
                    except ValueError:
                        measurement_value = None
                    self.data[measurement_name].append([time, measurement_value])

        # Clean up files
        #os.remove(self.filename)
        os.remove(os.path.join((self.benchmark.cwd or ''), self.filename))

        self.data["duration"] = (endtime - starttime).total_seconds()

        return self.data
# --- End test run for perf


Collector.register_collector("uprof", uProfCollector)
