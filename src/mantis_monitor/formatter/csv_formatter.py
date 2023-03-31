"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

import pandas
import csv

from mantis_monitor.formatter.formatter import Formatter

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
        # This is where the bug lives for extra ""
        data = pandas.read_csv(filename)
        return data

Formatter.register_formatter("CSV", CSVFormatter)
