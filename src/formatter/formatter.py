"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

# TODO - support extra pathing via config

class Formatter():
    """
    This is the generic form for a formatter; use as an interface
    Note all formatters begin in the native representation
    This is currently Python Pandas DataFrames
    """

    implementations = {}

    @staticmethod
    def register_formatter(name, formatter_class):
        Formatter.implementations[name] = formatter_class

    @staticmethod
    def get_formatter(name):
        return Formatter.implementations[name]()

    def __init__(self):
        self.name = ""
    
    def convert(self, data):
        pass

    def save(self, filename, data):
        pass

    def open(self, filename):
        pass
