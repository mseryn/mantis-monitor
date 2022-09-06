"""
Implementation of Mantis time-to-completion collector

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
import math
import subprocess
import os
import datetime

import pprint

from mantis_monitor.collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class TTCCollector(Collector):
    """
    This is the implementation of the wallclock time-to-completion collector
    """
    def __init__(self, configuration, iteration, benchmark):
        self.name = "TTCCollector"
        self.description = "Collector for measuring unimpeded time-to-completion"
        self.benchmark = benchmark
        self.iteration = iteration
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-ttc".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)
        self.data = []

        self.setup()

    def run_all(self):
        self.benchmark.before_each()

        self.data = {
            "benchmark_name": self.benchmark.name,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "units":          "s",
            "measurements":   "time_to_completion",
            "duration":       0,
        }

        starttime = datetime.datetime.now()
        process = subprocess.run(self.benchmark.get_run_command(), shell=True, cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()

        self.data["duration"] = (endtime - starttime).total_seconds()
        self.data = [self.data]

        self.benchmark.after_each()



Collector.register_collector("time_to_completion", TTCCollector)
