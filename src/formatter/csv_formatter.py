"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import pandas

from formatter.formatter import Formatter

class CSVFormatter(Formatter):
    def __init__(self):
        self.name = "CSV"

    def convert(self, data):
        # Not needed for this
        return data

    def save(self, filename, data):
        filename = filename + ".csv"
        data.to_csv(filename)

    def open(self, filename):
        data = pandas.read_csv(filename)
        return data

Formatter.register_formatter("CSV", CSVFormatter)
