"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging
import subprocess

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Benchmark():

    implementations = {}

    # create attributes for instances (not shared; immutable)
    cwd = None
    env = None

    @staticmethod
    def register_benchmark(name, benchmark_class):
        if name in Benchmark.implementations:
            logging.error("A benchmark named {} was supplied to be registered, but a benchmark by that name already exists".format(name))
            raise ValueError("Benchmark name collision")
        Benchmark.implementations[name] = benchmark_class

    @staticmethod
    def get_benchmarks(name, arguments):
        if name not in Benchmark.implementations:
            logging.error("A benchmark named {} was requested, but no benchmark by that name exists (is the configuration correct?)".format(name))
            return None
        return Benchmark.implementations[name].generate_benchmarks(arguments)

    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls(arguments)]

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
