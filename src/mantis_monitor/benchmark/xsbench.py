"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging
from mantis_monitor.benchmark.benchmark import Benchmark

logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class XSBench(Benchmark):
    def get_run_command(self):
        # ./location/XSBench -m event
        return_string = [self.location]
        return_string.extend(self.arguments)
        return " ".join(return_string)
        
class XSBenchCuda(XSBench):
    def __init__(self, arguments):
        self.arguments = ["-m event"]
        self.name = "XSBench_CUDA"
        self.description = "CUDA implementation of microbenchmark XSBench"

        self.location = arguments["loc"]

class XSBenchOpenmpOffload(XSBench):
    def __init__(self, arguments):
        self.arguments = ["-m event"]
        self.name = "XSBench_OpenMP_Offload"
        self.description = \
            "OpenMP offloading (GPU-offload) implementation of microbenchmark XSBench"

        self.location = arguments["loc"]

Benchmark.register_benchmark("XSBenchOpenmpOffload", XSBenchOpenmpOffload)
Benchmark.register_benchmark("XSBenchCuda", XSBenchCuda)
