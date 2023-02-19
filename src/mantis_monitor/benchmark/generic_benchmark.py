"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging
from mantis_monitor.benchmark.benchmark import Benchmark

class GenericBenchmark(Benchmark):

    def __init__(self, arguments):
        # mandatory is a name and a command to run
        if "cmd" not in arguments or "name" not in arguments:
            print("for a generic benchmark, must provide a name and cmd to run")
        self.run = arguments["cmd"]
        self.name = arguments["name"]
        if "cwd" in arguments:
            self.cwd = arguments["cwd"]

    def get_run_command(self):
        return self.run

Benchmark.register_benchmark("generic_benchmark", GenericBenchmark)
