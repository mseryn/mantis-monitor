"""
Module containing Mantis base Benchmark class and any basic benchmark helper functions

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import logging

logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Benchmark():
    def __init__(location, arguments):
        self.location = location
        self.arguments = arguments
        self.name = ""
        self.description = ""

    def setup(self):
        pass

    def get_run_command(self):
        pass

    def teardown(self):
        pass
