"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import pickle
import pandas

from formatter.formatter import Formatter

class PandasPickleFormatter(Formatter):
    def __init__(self):
        self.name = "PandasPickle"
    
    def convert(self, data):
        # Not needed for this
        return data

    def save(self, filename, data):
        filename = filename + ".pkl"
        data.to_pickle(filename)

    def open(self, filename):
        data = pandas.read_pickle(filename)
        return data

Formatter.register_formatter("PandasPickle", PandasPickleFormatter)
