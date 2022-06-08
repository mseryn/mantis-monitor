"""
Implementation of Mantis perf collector

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
import math
import subprocess
import os

import pprint

from collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class PerfCollector(Collector):
    """
    This is the implementation of the perf data collector
    """
    
    def __init__(self, configuration, iteration, benchmark):
        self.name = "PerfCollector"
        self.description = "Collector for configuring perf metric collection"
        self.benchmark = benchmark
        self.iteration = iteration
        self.counters = configuration.perf_counters
        self.pmu_count = configuration.collector_modes["perf"]["pmu_count"]
        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-perfrun_{{perfrun_count}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)
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
                self.benchmark, current_filename, self.iteration)
            self.testruns.append(current_testrun)

            self.global_ID = self.global_ID + 1

    def run_all(self):
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = this_testrun.run()
            this_testrun.benchmark.after_each()
            self.data.append(data)


        print("in perf run all")
        print(self.data)

# --- Begin test run for perf
class PerfTestRun():
    """
    This is the implementation of the perf data testrun
    """
    def __init__(self, name, counters, timescale, benchmark, filename, iteration):
        self.name = name
        self.counters = counters
        self.timescale = timescale
        self.benchmark = benchmark
        self.filename = filename
        self.iteration = iteration
        self.runstring = "perf stat -x , -a -e {} -I {} -o {} {}"
        self.counters_string = ",".join(self.counters)
        self.runcommand = self.runstring.format(self.counters_string, self.timescale, self.filename, \
            self.benchmark.get_run_command())
        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "units":            "count per timescale milliseconds", \
                        "measurements": self.counters, \
                        }
        for counter in self.counters:
            self.data[counter] = []

    def run(self):
        # Run it
        #logging.info("running following command:")
        #logging.info(self.runcommand)

        runcommand_parts = self.runcommand.split(" ")
        discarded_output = subprocess.run(runcommand_parts, capture_output=True)

        # Collect data
        with open(self.filename, 'r') as csvfile:
            for line in csvfile:
                line = line.strip().split(",")
                if len(line) > 1 and "#" not in line[0]:
                    time = float(line[0])
                    measurement_name = line[3]
                    measurement_value = float(line[1])
                    self.data[measurement_name].append((time, measurement_value))

        # Clean up files
        os.remove(self.filename)

        print("in perf testrun")
        print(self.data)
        return self.data
# --- End test run for perf


Collector.register_collector("perf", PerfCollector)
