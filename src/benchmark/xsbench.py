"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
from benchmark.benchmark import Benchmark

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class XSBench(Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls({"type": typestr}) for typestr in arguments["types"]]

    def get_run_command(self):
        return "/home/mcorneli/xsbench/{location}/XSBench -m event".format(location = self.location)
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
