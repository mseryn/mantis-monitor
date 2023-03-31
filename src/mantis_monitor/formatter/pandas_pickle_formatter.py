"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016-2023 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""

import pickle
import pandas

from mantis_monitor.formatter.formatter import Formatter

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
