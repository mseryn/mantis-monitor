"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016-2023 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""

import logging
from mantis_monitor.benchmark.benchmark import Benchmark

class GenericBenchmark(Benchmark):

    def __init__(self, arguments):
        # mandatory is a name and a command to run
        if "cmd" not in arguments or "name" not in arguments:
            print("for a generic benchmark, must provide a name and cmd to run")
        self.run = arguments["cmd"]
        self.name = arguments["name"]
        if "cwd" in arguments:
            self.cwd = arguments["cwd"]

    def get_run_command(self):
        return self.run

Benchmark.register_benchmark("generic_benchmark", GenericBenchmark)
