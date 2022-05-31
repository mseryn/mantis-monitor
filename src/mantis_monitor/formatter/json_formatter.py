"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import pandas

from mantis_monitor.formatter.formatter import Formatter

class JSONFormatter(Formatter):
    def __init__(self):
        self.name = "CSV"
    
    def convert(self, data):
        # Not needed for this
        return data

    def save(self, filename, data):
        filename = filename + ".json"
        data.to_json(filename)

    def open(self, filename):
        data = pandas.read_json(filename)
        return data


Formatter.register_formatter("JSON", JSONFormatter)
