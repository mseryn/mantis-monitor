"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import pickle
import pandas
#import sqlalchemy

# TODO - support extra pathing via config

class Formatter():
    """
    This is the generic form for a formatter; use as an interface
    Note all formatters begin in the native representation
    This is currently Python Pandas DataFrames
    """
    def __init__(self):
        self.name = ""
    
    def convert(self, data):
        pass

    def save(self, filename, data):
        pass

    def open(self, filename):
        pass


#---
class PandasPickle(Formatter):
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

#---
class CSV(Formatter):
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

#---
class JSON(Formatter):
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
