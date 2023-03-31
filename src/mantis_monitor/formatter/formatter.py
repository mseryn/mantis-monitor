"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
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
