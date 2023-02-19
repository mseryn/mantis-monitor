"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging
import math
import subprocess
import os

import pprint

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Collector():
    """
    This is the generic form for a collector; use as an interface
    class TestRun():
        def __init__(self,name):
            self.name = name

        def return_run_command(self):
            return ""

        def run(self):
            pass
    """
    implementations = {}

    @staticmethod
    def register_collector(name, collector_class):
        if name in Collector.implementations:
            logging.error("A collector named {} was supplied to be registered, but a collector by that name already exists".format(name))
            raise ValueError("Collector name collision")
        Collector.implementations[name] = collector_class

    @staticmethod
    def get_collector(name, configuration, iteration, benchmark, benchmark_set):
        if name not in Collector.implementations:
            logging.error("A collector named {} was requested, but no collector by that name exists (is the configuration correct?)".format(name))
            return None
        return Collector.implementations[name](configuration, iteration, benchmark, benchmark_set)



    def __init__(self, configuration, iteration, benchmark, benchmark_set = "solo"):
        self.name = ""
        self.description = ""
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.configuration = configuration
        self.testruns = []

        self.setup()

    def setup(self):
        pass

    async def run_all(self):
        yield None

