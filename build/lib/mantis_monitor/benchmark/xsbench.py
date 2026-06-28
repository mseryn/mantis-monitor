# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is

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
This file contains the implementation of the XSBench benchmark.

XSBench can be found here: https://github.com/ANL-CESAR/XSBench

This class is an example of a specific codebase implemented as a 
benchmark by directly inheriting from the Benchmark class.
This allows for more sophisticated action and simpler config.yaml
options.
Implementing a custom Benchmark is recommended for users who intend
to use mantis-monitor repetedly and want to leverage their codebase
in complex ways.
Most users will interface with the Benchmark class system transparently
through options given in config.yaml.

Users looking to implement their own Benchmark may use this class as
an example, as it is maintained alongside changes to mantis-monitor.
Many elements in this example are a bit overbuilt as an attempt
to demonstrate some uses of the Benchmark class.
"""
from mantis_monitor.benchmark.benchmark import Benchmark
import mantis_monitor

class XSBench(Benchmark):
    """
    This is the implementation of the XSBench Benchmark.

    It inherits directly from the Benchmark() class.

    :ivar location: The subdirectory to use when running this instance
    :ivar typestr: The type of XSBench to run (CUDA, openmp-threading, etc)
    :ivar name: The formatted name to use based on the typestr
    """

    @classmethod
    def generate_benchmarks(cls, arguments):
        """
        Generate the requested types of XSBench runs

        :return: A list of XSBench objects to run
        """
        return [cls({"type": typestr}) for typestr in arguments["types"]]

    def get_run_command(self):
        """
        Return the string to run for this XSBench run

        :return: the command string appropriately populated
        """
        return "/home/mseryn/XSBench/{location}/XSBench -m event".format(location = self.location)

    def __init__(self, arguments):
        """
        Init the object

        :param arguments: A dict of arguments given in config.yaml
        """
        self.typestr = arguments["type"]
        self.name = "XSBench_{typestr}".format(typestr = self.typestr)
        locations = {"cuda": "cuda", \
                    "openmp-offload": "openmp-offload", \
                    "openmp-threading": "openmp-threading",\
                    }
        self.location = locations[self.typestr]

Benchmark.register_benchmark("XSBench", XSBench)
