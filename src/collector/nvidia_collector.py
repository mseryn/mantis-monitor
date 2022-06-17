"""
Implementation of Mantis nvidia SMI collector

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

class NvidiaCollector(Collector):
    """
    This is the implementation of the nvidia tool data collector
    """
    
    def __init__(self, configuration, iteration, benchmark):
        self.name = "NvidiaCollector"
        self.description = "Collector for configuring nvidia profiling metric collection"
        self.benchmark = benchmark
        self.iteration = iteration

        self.modes = configuration.collector_modes["nvidia"]["modes"]
        self.gen = configuration.collector_modes["nvidia"]["gen"]

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-nvidia_{{nvidia_identifier}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)
        self.data = []
        self.global_ID = 0

        self.setup()


    def setup(self):
        if "power_summary" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "power_summary")
            self.testruns.append(PowerSummaryTestRun("nvidiapowersummary", self.benchmark, current_filename, self.iteration, self.timescale))

        # add more here as more modes supported

    def run_all(self):
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = this_testrun.run()
            this_testrun.benchmark.after_each()
            self.data.append(data)


class PowerSummaryTestRun():
    """
    This is the implementation of the power summary nvidia testrun
    Makes use of summary mode for nvidia-smi
    """
    def __init__(self, name, benchmark, filename, iteration, timescale):
        self.name = name
        self.benchmark = benchmark
        self.filename = filename
        self.iteration = iteration
        self.timescale = timescale

        self.smi_runstring = "nvidia-smi --query-gpu=timestamp,index,power.draw --loop-ms=1000 --format=csv > {filename}.csv"
        self.smi_runcommand = self.smi_runstring.format(filename = self.filename)
        self.bench_runcommand = self.benchmark.get_run_command()
        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "units":            "count per timescale milliseconds", \
                        "measurements": ["not sure"], \
                        }

    def run(self):
        # Run it

        # Start SMI
        smi_proc = subprocess.Popen(self.smi_runcommand.split(" "))

        # Run benchmark
        discarded_output = subprocess.run(self.bench_runcommand.split(" "), capture_output=True)

        # Kill SMI
        smi_proc.kill()

        """
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
        """
        return []



# --- End test run for perf


Collector.register_collector("nvidia", NvidiaCollector)
