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

class PFSCollector(Collector):
    """
    This is the implementation of the nvidia tool data collector
    """
    
    def __init__(self, configuration, iteration, benchmark):
        self.name = "PFSCollector"
        self.description = "Collector for configuring proc filesystem metric collection"
        self.benchmark = benchmark
        self.iteration = iteration

        self.measurements = configuration.collector_modes["utilization"]

        # set up units - better way?
        units = {"default":             "unknown",
                 "cpu_utilization":     "(time, pct)",
                 "memory_utilization":  "(time, pct)",
                }

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-utilization".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)
        self.data = []


    def run_all(self):
        this_testrun.benchmark.before_each()

        data = PFSTimeTestRun("Utilization", self.benchmark, current_filename, self.iteration, self.timescale, \
            self.measurements, "unknown").run()

        this_testrun.benchmark.after_each()
        if isinstance(data, list):
            self.data.extend(data)
        else:
            self.data.append(data)

class PFSTimeTestRun():
    """
    This is the generic Proc FS testrun to collect utilization measurements over time
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
        self.smi_runstring = "nvidia-smi --query-gpu=timestamp,index,{measure} --loop-ms=1000 --format=csv,noheader,nounits"
        self.smi_runcommand = self.smi_runstring.format(filename = self.filename, measure = measurements_string)
        self.bench_runcommand = self.benchmark.get_run_command()
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
        starttime = datetime.now()

        code_proc = subprocess.Popen(self.bench_runcommand.split(" "), executable="/bin/bash", env=self.benchmark.env, cwd=self.benchmark.cwd)

        while (code_proc.poll() is None):
            time = datetime.now()
            cpu_val = psutil.cpu_percent(interval=None, percpu=True)
            cpu_vals[time] = cpu_val
            mem = psutil.virtual_memory().used
            mem_vals.append((time, mem_val))

        endtime = datetime.now()

        # Collect data
        if "memory_utilization" in self.measurements:
            self.data["memory_utilization"] = mem_vals

        if "cpu_utilization" in self.measurements:
            for i in range(0, cpu_count):
                column = "cpu_{index}_utilization".format(index = i)
                parsed_data = [(x, y[i]) for x, y in cpu_vals.items()]
                self.data[column] = parsed_data

        duration = endtime - starttime  
        self.data["duration"] = duration.total_seconds()

        return self.data

Collector.register_collector("utilization", PFSCollector)
