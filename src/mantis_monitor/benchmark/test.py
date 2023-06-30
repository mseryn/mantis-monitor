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
This file contains an implementation of a simple test benchmark.

This benchmark is used for test purposes, and it is an example
of leveraging some of the available function calls built into
the Benchmark class.
"""
from mantis_monitor.benchmark.benchmark import Benchmark

class TestBench(Benchmark):
    """
    This benchmark is used for test purposes, and it is an example
    of leveraging some of the available function calls built into
    the Benchmark class.

    It inherits directly from the Benchmark class.
    
    :ivar time: The amount of time the sleep command runs for
    :ivar name: The formatted name to use based on the time
    """
    @classmethod
    def generate_benchmarks(cls, arguments):
        """
        Generate the requested types of test benchmark runs

        :return: A list of TestBench objects to run
        """

        return [cls({"time": time}) for time in arguments["waittimes"]]

    def before_each(self):
        """
        A set of strings to run before every TestBench run command
        """
        print("echo running this before each test bench run")
        print("running test bench with time {time} sec".format(time = self.time))

    def after_each(self):
        """
        A set of strings to run after every TestBench run command
        """
        print("echo running this after each test bench run")

    def before_all(self):
        """
        A set of strings to run before any TestBench is run
        
        This only runs once even if many TestBench objects run in a row.
        """
        print("echo running this before each test bench configuration")

    def after_all(self):
        """
        A set of strings to run after any TestBench is run
        
        This only runs once even if many TestBench objects run in a row.
        """
        print("echo running this after each test bench configuration")

    def get_run_command(self):
        """
        Returns the command to run

        :return: a string command to run for the appropriate amount of time
        """
        return "sleep {time}".format(time = self.time)

    def __init__(self, arguments):
        """
        Init the object

        :param arguments: a dictionary of arguments given to the Benchmark via
        the config.yaml
        """
        self.time = arguments["time"]
        self.name = "TestBench_time{time}s".format(time = self.time)

Benchmark.register_benchmark("TestBench", TestBench)
