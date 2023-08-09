"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016-2023 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""

import logging
import math
import subprocess
import os
import asyncio

import pprint

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Collector():
    """
    This is the generic form for a collector; use as an interface
    class TestRun():
        def __init__(self,name):
            self.name = name

        def return_run_command(self):
            return ""

        def run(self):
            pass
    """
    implementations = {}

    @staticmethod
    def register_collector(name, collector_class):
        if name in Collector.implementations:
            logging.error("A collector named {} was supplied to be registered, but a collector by that name already exists".format(name))
            raise ValueError("Collector name collision")
        Collector.implementations[name] = collector_class

    @staticmethod
    def get_collector(name, configuration, iteration, benchmark, benchmark_set):
        if name not in Collector.implementations:
            logging.error("A collector named {} was requested, but no collector by that name exists (is the configuration correct?)".format(name))
            return None
        return Collector.implementations[name](configuration, iteration, benchmark, benchmark_set)



    def __init__(self, configuration, iteration, benchmark, benchmark_set = "solo"):
        self.name = ""
        self.description = ""
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.configuration = configuration
        self.testruns = []

        self.setup()

    def setup(self):
        pass

    async def run_all(self):
        yield None

    async def run_bare(self):
        process = await asyncio.create_subprocess_shell(self.benchmark.get_run_command(), cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()

