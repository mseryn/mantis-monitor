"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging
import math

logging.basicConfig(filename='testing.log', encoding='utf-8', \
    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Collector():
    """
    This is the generic form for a collector; use as an interface
    """
    def __init__(self,configuration):
        self.name = ""
        self.description = ""
        self.benchmarks = []
        self.configuration = configuration
        self.testruns = []

        self.setup()

    def setup(self):
        pass


class TestRun():
    """
    This is the generic form for a testrun as controlled by a collector;
    use as an interface
    """
    def __init__(self,name):
        self.name = name

    def return_run_command(self):
        return ""


#--- Perf collector components ---

class PerfCollector(Collector):
    """
    This is the implementation of the perf data collector
    """
    def __init__(self, configuration, iteration, benchmark):
        self.name = "PerfCollector"
        self.description = "Collector for configuring perf metric collection"
        self.benchmark = benchmark
        self.counters = configuration.perf_counters
        self.pmu_count = configuration.pmu_count
        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-perfrun_{{perfrun_count}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)

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
            current_testrun = PerfTestRun(str(i), counters_list, self.timescale,\
                self.benchmark, current_filename)
            self.testruns.append(current_testrun)
            

class PerfTestRun(TestRun):
    """
    This is the implementation of the perf data testrun
    """
    def __init__(self, name, counters, timescale, benchmark, filename):
        self.name = name
        self.counters = counters
        self.timescale = timescale
        self.benchmark = benchmark
        self.filename = filename
        self.runstring = "perf stat -x , -a -e {} -I {} -o {} {}"

    def return_run_command(self):
#    def return_run_command(self, filename):
        counters_string = ",".join(self.counters)
        return self.runstring.format(counters_string, self.timescale, self.filename, \
            self.benchmark.get_run_command())


#class NvidiaPowerCollector(Collector):

#class NvidiaMemoryCollector(Collector):

#class ProcFSCollector(Collector):
