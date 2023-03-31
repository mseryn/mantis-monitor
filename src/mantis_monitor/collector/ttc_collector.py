"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

#import logging
import math
import subprocess
import asyncio
import os
import datetime

import pprint

from mantis_monitor.collector.collector import Collector

class TTCCollector(Collector):
    """
    This is the implementation of the ttc data collector
    """

    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        self.name = "TTCCollector"
        self.description = "Collector for baseline ttc collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.testruns = []
        self.data = []
        self.global_ID = 0

        self.testruns.append(TTCTestRun(self.name, self.benchmark, self.iteration, self.benchmark_set))

    async def run_all(self):
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            self.data.append(data)
            yield


# --- Begin test run for perf
class TTCTestRun():
    """
    This is the implementation of the ttc data testrun
    """
    def __init__(self, name, benchmark, iteration, benchmark_set):
        self.name = name
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration
        self.runcommand = self.benchmark.get_run_command()
        self.data = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "units":          "seconds",
            "measurements":   "baseline_duration",
            "duration":       0,
        }

        self.duration = None

    async def run(self):
        # Run it

        starttime = datetime.datetime.now()
        process = await asyncio.create_subprocess_shell(self.runcommand, cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()
        # process = subprocess.run(self.runcommand, shell=True, cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()

        if process.returncode != 0:
            print('Oops, bad data...')
            return self.data

        self.data["duration"] = (endtime - starttime).total_seconds()

        return self.data
# --- End test run for perf


Collector.register_collector("ttc", TTCCollector)
