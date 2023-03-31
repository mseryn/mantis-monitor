"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

import logging
import subprocess

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Benchmark():

    implementations = {}

    # create attributes for instances (not shared; immutable)
    cwd = None
    env = None

    @staticmethod
    def register_benchmark(name, benchmark_class):
        if name in Benchmark.implementations:
            logging.error("A benchmark named {} was supplied to be registered, but a benchmark by that name already exists".format(name))
            raise ValueError("Benchmark name collision")
        Benchmark.implementations[name] = benchmark_class

    @staticmethod
    def get_benchmarks(name, arguments):
        if name not in Benchmark.implementations:
            logging.error("A benchmark named {} was requested, but no benchmark by that name exists (is the configuration correct?)".format(name))
            return None
        return Benchmark.implementations[name].generate_benchmarks(arguments)

    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls(arguments)]

    def __init__(self, arguments): #location = "", runscript = "", arguments = "", name = ""):
        self.name = ""
        self.arguments = None

    def before_all(self):
        pass
    def before_each(self):
        pass
    def get_run_command(self):
        pass
    def after_all(self):
        pass
    def after_each(self):
        pass
