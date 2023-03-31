"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016-2023 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

import mantis_monitor

class ExternalTestBench(mantis_monitor.benchmark.benchmark.Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls({"time": time}) for time in arguments["waittimes"]]

    def before_each(self):
        print("echo running this before each test bench run")
        print("running EXTERNAL CLASS test bench with time {time} sec".format(time = self.time))

    def after_each(self):
        print("echo running this after each test bench run")

    def before_all(self):
        print("echo running this before each test bench configuration")

    def after_all(self):
        print("echo running this after each test bench configuration")

    def get_run_command(self):
        return "sleep {time}".format(time = self.time)

    def __init__(self, arguments):
        self.time = arguments["time"]
        self.name = "TestBench_time{time}s".format(time = self.time)

mantis_monitor.monitor.run_with(ExternalTestBench)
