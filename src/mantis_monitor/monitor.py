"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.
"""

from mantis_monitor import benchmark
from mantis_monitor import configuration
from mantis_monitor import collector
from mantis_monitor import formatter

import pandas
#import logging
import argparse
import pprint
import sys
import collections.abc
import asyncio

async def main():
    """
    Main run script for Mantis Monitor
    """
    parser = argparse.ArgumentParser(
                        prog = 'Mantis-Monitor',
                        description = 'Monitoring suite for program performance profiling',
                        epilog = 'Please contact melanie.e.cornelius@gmail.com for additional information.')

    parser.add_argument("config", type=str,
                        help="Location of configuration file")
    parser.add_argument("--log", type=bool, default=False, 
                        help="print logs to file, defaults to false")
    parser.add_argument("--v", action="store_true",
                        help="print verbose information to std out")

    args = parser.parse_args()

    config_location = args.config
    config = configuration.Configuration(location=config_location)
    config.print_all()

    all_dataframes = []
    dataframe_columns = ["benchmark_name", "collector_name", "iteration", "timescale", "units", "measurements"]
    data = pandas.DataFrame(columns = dataframe_columns)

    run_benchmarks = []
    
    # Process benchmark matrix configuration
    if isinstance(config.benchmark_matrix, collections.abc.Sequence):
        bench_sets = []
        for benchmark_set in config.benchmark_matrix:
            benchmarks = []
            for bench in benchmark_set:
                bench_datas = [ b for b in config.contents["benchmarks"] if b["name"] == bench ]
                if len(bench_datas) != 1:
                    raise Exception("Could not match benchmark name " + bench + " to a single configured benchmark")
                bench_data = bench_datas[0]
                if "type" not in bench_data:
                    bench_data["type"] = "generic_benchmark"
                benchmarks.extend(benchmark.benchmark.Benchmark.get_benchmarks(bench_data["type"], bench_data))
            bench_sets.append((':'.join(benchmark_set),benchmarks))
        run_benchmarks = bench_sets
    else:
        for bench in config.contents["benchmarks"]:
            if "type" not in bench:
                bench["type"] = "generic_benchmark"
            print("Adding benchmark ", bench["type"], bench["name"])
            run_benchmarks.extend(benchmark.benchmark.Benchmark.get_benchmarks(bench["type"], bench) or [])

    run_collectors = []
    for each_benchmark in run_benchmarks:
        benchmarks = each_benchmark
        if type(benchmarks) is not tuple:
            benchmarks = ('solo', [benchmarks])

        for bench in benchmarks[1]:
            bench.before_all()

        for iteration in range(config.iterations):
            for mode in config.collector_modes:
                generators = []
                collectors = []
                for bench in benchmarks[1]:
                    this_collector = collector.collector.Collector.get_collector(mode, config, iteration, bench, benchmarks[0])
                    if this_collector:
                        collectors.append(this_collector)
                        generators.append(this_collector.run_all())
                running_collectors = True
                while running_collectors:
                    testruns = list(map(lambda x: x.asend(None), generators))
                    print("Running testruns:", testruns)
                    results = await asyncio.gather(*testruns, return_exceptions=True)
                    print("Results:", results)
                    running_collectors = False
                    for result in results:
                        if not isinstance(result, StopAsyncIteration):
                            running_collectors = True
                    

                for this_collector in collectors:
                    new_data = pandas.DataFrame(this_collector.data)
                    data = pandas.concat([data, new_data])

        for bench in benchmarks[1]:
            bench.after_all()

    data = data.reset_index()

    filename = config.test_name
    if config.formatter_modes:
        for mode in config.formatter_modes:
            this_formatter = formatter.formatter.Formatter.get_formatter(mode)
            converted_data = this_formatter.convert(data)
            print(type(converted_data))
            print(converted_data)
            this_formatter.save(filename, converted_data)

def run():
    asyncio.run(main())

def run_with(*classes):
    """
        Hannah, what is this?
    """
    for c in classes:
        benchmark.benchmark.Benchmark.register_benchmark(c.__name__, c)
    run()

if __name__ == "__main__":
    run()
