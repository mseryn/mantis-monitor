"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging
import subprocess

logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Benchmark():

    implementations = {}

    # Make sure this is unique TODO
    @staticmethod
    def register_benchmark(name, benchmark_class):
        Benchmark.implementations[name] = benchmark_class

    @staticmethod
    def get_benchmark_class(name):
        return Benchmark.implementations[name]

    @classmethod
    def generate_benchmarks(arguments):
        pass

    def __init__(self, arguments): #location = "", runscript = "", arguments = "", name = ""):
        self.name = ""
        self.arguments = None

    def before_all(self):
        pass
    def before_each(self):
        pass
    def get_run_command(self):
        pass
    def after_all(self):
        pass
    def after_each(self):
        pass
