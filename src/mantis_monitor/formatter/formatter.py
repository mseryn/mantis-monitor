# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is 
# copyright (C) 2016-2023 by Melanie Cornelius.

# Mantis is free software: 
# you can redistribute it and/or modify it under the terms of the GNU Lesser 
# General Public License as published by the Free Software Foundation,     
# either version 3 of the License, or (at your option) any later version.

# Mantis is distributed in the hope that it will be useful, but WITHOUT 
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or 
# FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along 
# with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""
In mantis-monitor, Formatters are objects implementing input and output
from the Unified Data Format (UDF) to some other format.

Natively-supported formats currently include:
    - CSV
    - JSON
    - Pandas DataFrame (pickled)

To implement a new Formatter, inherit from the Formatter() class, and
overwrite functions as needed.

TODO - support extra pathing via config
"""

class Formatter():
    """
    This is the generic form for a formatter; use as an interface

    :cvar implementations: List of all registered Formatter classes
    :type implementations: list
    """

    implementations = {}

    @staticmethod
    def register_formatter(name, formatter_class):
        """
        Register a new formatter class

        Call this at the end of your new-formatter.py file

        :param name: New name for the formatter
        :type name: str
        :param formatter_class: Formatter class made for registration
        :type formatter_class: Formatter()
        """
        Formatter.implementations[name] = formatter_class

    @staticmethod
    def get_formatter(name):
        """
        Using the string name of a Formatter implementation, return the object

        :param name: Name of the Formatter to return
        :type name: str

        :return: Formatter.implementations[name]()
        :rtype: Formatter() class object
        """

    def __init__(self):
        """
        Init the object

        Sets the name to an empty string
        """
        self.name = ""

    def save(self, filename, data):
        """
        Take the UDF and transform it to the desired Formatter file format
        or type

        :param filename: Path to the location of the new file
        :type filename: str

        :param data: UDF Pandas DataFrame
        :type data: pandas.DataFrame()

        :return: None
        """
        pass

    def open(self, filename):
        """
        Take the Formatter file format or type and transform it to the UDF

        :param filename: Path to the location of the file to read
        :type filename: str

        :return: None
        """
        pass

__all__ = ['Formatter']
