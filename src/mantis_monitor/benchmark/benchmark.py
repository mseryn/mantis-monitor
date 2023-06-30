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
In mantis-monitor, Benchmarks are objects containing instructions
for initializing and running user code.

For most purposes, users should simply use the config.yaml file
with simple configuration options, such as:
- environment variables
- runtime command and options
- venv use
- run directory

These elements are exemplified in the given example config.yaml files 
and are implemented in the GenericBenchmark class.

For complicated or involved uses, users are welcome to extend this
Benchmark interface for their own purposes. An example of such
an extension can be found in XSBench - a custom class to run the
ECP proxy app XSBench.
"""

import logging
import subprocess

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Benchmark():
    """
    This is the generic form of a benchmark, the term used in mantis-monitor
    to describe user code to monitor. Use this as an interface if needed. 

    In general, users likely only need use the config.yaml file. This abstracts
    use of the GenericBenchmark, so users don't usually need to be aware of 
    this class.

    :cvar implementations: List of all registered Collector classes
    :type implementations: list
    :cvar cwd: Working directory for this benchmark, if any given
    :type cwd: str
    :cvar env: Environment to use for this benchmark, if any
    :type env: str
    """

    implementations = {}

    # create attributes for instances (not shared; immutable)
    cwd = None
    env = None

    @staticmethod
    def register_benchmark(name, benchmark_class):
        """
        Register a new Benchmark class

        Call this at the end of your new_benchmark.py file

        :param name: New name for the Benchmark
        :type name: str
        :param benchmark_class: Benchmark class made for registration
        :type benchmark_class: Benchmark()
        """
        if name in Benchmark.implementations:
            logging.error("A benchmark named {} was supplied to be registered, but a benchmark by that name already exists".format(name))
            raise ValueError("Benchmark name collision")
        Benchmark.implementations[name] = benchmark_class

    @staticmethod
    def get_benchmarks(name, arguments):
        """
        Using the string name of a Benchmark implementation, return the object

        :param name: Name of the Benchmark to return
        :type name: str

        :return: Benchmark.implementations[name]()
        :rtype: Benchmark()
        """
        if name not in Benchmark.implementations:
            logging.error("A benchmark named {} was requested, but no benchmark by that name exists (is the configuration correct?)".format(name))
            return None
        return Benchmark.implementations[name].generate_benchmarks(arguments)

    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls(arguments)]

    def __init__(self, arguments): #location = "", runscript = "", arguments = "", name = ""):
        """
        Init the object

        :param arguments: Arguments to use during runtime
        :type arguments: str
        """

        self.name = ""
        self.arguments = None

    def before_all(self):
        """
        Anything to handle before running any instance of this benchmark
        """
        pass

    def before_each(self):
        """
        Anything to handle before running each instance of this benchmark
        """
        pass

    def get_run_command(self):
        """
        Return the populated run command for this Benchmark
        """
        pass

    def after_all(self):
        """
        Anything to handle after running each instance of this benchmark
        """
        pass

    def after_each(self):
        """
        Anything to handle after running any instance of this benchmark
        """
        pass
