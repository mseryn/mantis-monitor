"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

#import logging
import math
import subprocess
import asyncio
import os
import datetime

import pprint

from mantis_monitor.collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class PerfCollector(Collector):
    """
    This is the implementation of the perf data collector
    """

    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        self.name = "PerfCollector"
        self.description = "Collector for configuring perf metric collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.counters = configuration.perf_counters
        self.pmu_count = configuration.collector_modes["perf"]["pmu_count"]
        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-set_{benchsetstring}-perfrun_{{perfrun_count}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name, benchsetstring = self.benchmark_set)
        self.data = []
        self.global_ID = 0

        self.setup()


    def setup(self):
        num_perf_counters = len(self.counters)
        num_perf_testruns = math.ceil(num_perf_counters / self.pmu_count)

        for i in range(0, num_perf_testruns):
            # NOTE - name is currently just the perf iteration count, make this meaningful later if needed
            start = i * self.pmu_count
            stop = min(num_perf_counters, ((i+1) * self.pmu_count))
            counters_list = self.counters[start:stop]
            current_filename = self.filename.format(perfrun_count = i)
            name = "_".join([self.name, str(self.global_ID)])
            current_testrun = PerfTestRun(name, counters_list, self.timescale,\
                self.benchmark, current_filename, self.iteration, self.benchmark_set)
            self.testruns.append(current_testrun)

            self.global_ID = self.global_ID + 1

    async def run_all(self):
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            self.data.append(data)
            yield


# --- Begin test run for perf
class PerfTestRun():
    """
    This is the implementation of the perf data testrun
    """
    def __init__(self, name, counters, timescale, benchmark, filename, iteration, benchmark_set):
        self.name = name
        self.counters = counters
        self.timescale = timescale
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.filename = filename
        self.iteration = iteration
        self.runstring = "perf stat -x , -a -e {} -I {} -o {} {}"
        self.counters_string = ",".join(self.counters)
        self.runcommand = self.runstring.format(self.counters_string, self.timescale, self.filename, \
            self.benchmark.get_run_command())
        self.data = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "timescale":      self.timescale,
            "units":          "count per timescale milliseconds",
            "measurements":   self.counters,
            "duration":       0,
        }
        self.duration = None
        for counter in self.counters:
            self.data[counter] = []

    async def run(self):
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


Collector.register_collector("perf", PerfCollector)
