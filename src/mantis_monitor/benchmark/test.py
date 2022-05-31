"""
Module containing test benchmark

This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
from benchmark.benchmark import Benchmark
import subprocess

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class TestBench(Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls({"time": time}) for time in arguments["waittimes"]]

    def before_each(self):
        print("echo running this before each test bench run")
        print("running test bench with time {time} sec".format(time = self.time))

    def after_each(self):
        print("echo running this after each test bench run")

    def before_all(self):
        print("echo running this before each test bench configuration")

    def after_all(self):
        print("echo running this after each test bench configuration")

    def get_run_command(self):
        return "sleep {time}".format(time = self.time)

    def __init__(self, arguments):
        self.time = arguments["time"]
        self.name = "TestBench_time{time}s".format(time = self.time)

Benchmark.register_benchmark("TestBench", TestBench)
