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
This file contains the implementation of the generic benchmark.

This benchmark functions as the typical interface to the user's
code, and it's transparent for most user use cases. The user
need only configure the config.yaml (documented elsewhere)
and generic benchmarks are automatically used.
"""

from mantis_monitor.benchmark.benchmark import Benchmark

class GenericBenchmark(Benchmark):
    """
    This is the implementation of the Generic Benchmark.

    It inherits directly from the Benchmark() class.

    :ivar run: Command to run this benchmark
    :ivar cwd: Optional working directory
    :ivar env: Optional enviornment variables to set or venv to activate
    """


    def __init__(self, arguments):
        """
        Init the object
        
        :param arguments: Dict containing all elements given to this benchmark in the config.yaml
        :type arguments: dictionary
        """
        # mandatory is a name and a command to run
        if "cmd" not in arguments or "name" not in arguments:
            print("for a generic benchmark, must provide a name and cmd to run")
        self.run = arguments["cmd"]
        self.name = arguments["name"]
        if "cwd" in arguments:
            self.cwd = arguments["cwd"]
        if "env" in arguments:
            self.env = arguments["env"]

    def get_run_command(self):
        """
        Get the run command

        :return: string of the command to run
        """
        return self.run

Benchmark.register_benchmark("generic_benchmark", GenericBenchmark)
