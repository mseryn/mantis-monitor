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

logging.basicConfig(filename='testing.log', encoding='utf-8', \
    format='%(levelname)s:%(message)s', level=logging.DEBUG)

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
    implementations = []

    @staticmethod
    def register_collector(name, collector_class):
        implementations[name] = collector_class

    @staticmethod
    def get_collector(name):
        return implementations[name]


    def __init__(self,configuration):
        self.name = ""
        self.description = ""
        self.benchmarks = []
        self.configuration = configuration
        self.testruns = []

        self.setup()

    def setup(self):
        pass

    def run_all(self):
        pass

