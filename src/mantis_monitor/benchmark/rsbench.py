"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

#import logging
from mantis_monitor.benchmark.benchmark import Benchmark
import mantis_monitor

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class RSBench(Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls({"type": typestr}) for typestr in arguments["types"]]

    def get_run_command(self):
        return "/home/mseryn/RSBench/{location}/rsbench -m event".format(location = self.location)
#        return "sleep {time}".format(time = self.time)

    def __init__(self, arguments):
        self.typestr = arguments["type"]
        #self.time = arguments["time"]
        #self.name = "TestBench_time{time}s".format(time = self.time)
        self.name = "RSBench_{typestr}".format(typestr = self.typestr)
        locations = {"cuda": "cuda", \
                    "openmp-offload": "openmp-offload", \
                    "openmp-threading": "openmp-threading",\
                    }
        self.location = locations[self.typestr]

Benchmark.register_benchmark("RSBench", RSBench)
