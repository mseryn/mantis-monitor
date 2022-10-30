"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
from mantis_monitor.benchmark.benchmark import Benchmark
import mantis_monitor

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class XSBench(Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls({"type": typestr}) for typestr in arguments["types"]]

    def get_run_command(self):
        return "/home/mseryn/XSBench/{location}/XSBench -m event".format(location = self.location)
#        return "sleep {time}".format(time = self.time)

    def __init__(self, arguments):
        self.typestr = arguments["type"]
        #self.time = arguments["time"]
        #self.name = "TestBench_time{time}s".format(time = self.time)
        self.name = "XSBench_{typestr}".format(typestr = self.typestr)
        locations = {"cuda": "cuda", \
                    "openmp-offload": "openmp-offload", \
                    "openmp-threading": "openmp-threading",\
                    }
        self.location = locations[self.typestr]

Benchmark.register_benchmark("XSBench", XSBench)

"""
 13 
 14 class TestBench(Benchmark):
 15     @classmethod
 16     def generate_benchmarks(cls, arguments):
 17         return [cls({"time": time}) for time in arguments["waittimes"]]
 18 
 19     def before_each(self):
 20         print("echo running this before each test bench run")
 21         print("running test bench with time {time} sec".format(time = self.time))
 22 
 23     def after_each(self):
 24         print("echo running this after each test bench run")
 25 
 26     def before_all(self):
 27         print("echo running this before each test bench configuration")
 28 
 29     def after_all(self):
 30         print("echo running this after each test bench configuration")
 31 
 32     def get_run_command(self):
 33         return "sleep {time}".format(time = self.time)
 34 
 35     def __init__(self, arguments):
 36         self.time = arguments["time"]
 37         self.name = "TestBench_time{time}s".format(time = self.time)
 38 
 39 Benchmark.register_benchmark("TestBench", TestBench)

"""
