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
        run_these_benchmarks = []
        for time in arguments["waittimes"]:
            run_these_benchmarks.append(TestBench({"time":time}))
        return run_these_benchmarks

    def before_each(self):
        components = 'echo "running this before each test bench run"'
        subprocess.run(components.split(" "))

    def after_each(self):
        components = 'echo "running this after each test bench run"'
        subprocess.run(components.split(" "))

    def before_all(self):
        components = 'echo "running this before ALL test bench runs"'
        subprocess.run(components.split(" "))

    def after_all(self):
        components = 'echo "running this after ALL test bench runs"'
        subprocess.run(components.split(" "))

    def get_run_command(self):
        components = "echo 'running test bench with time {time} sec".format(time = self.time)
        subprocess.run(components.split(" "))
        return("sleep {time}".format(time = self.time))

    def __init__(self, arguments):
        self.time = arguments["time"]
        self.name = "TestBench_time{time}s".format(time = self.time)

Benchmark.register_benchmark("TestBench", TestBench)
