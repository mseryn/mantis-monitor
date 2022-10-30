from mantis_monitor import benchmark
from mantis_monitor import configuration
from mantis_monitor import collector
from mantis_monitor import formatter

import pandas
#import logging
import argparse
import pprint
import sys

def run():
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
    for name, arguments in config.contents["benchmarks"].items():
        run_benchmarks.extend(benchmark.benchmark.Benchmark.get_benchmarks(name, arguments) or [])

    run_collectors = []
    for each_benchmark in run_benchmarks:

        each_benchmark.before_all()

        for iteration in range(config.iterations):
            for mode in config.collector_modes:
                this_collector = collector.collector.Collector.get_collector(mode, config, iteration, each_benchmark)
                if this_collector:
                    this_collector.run_all()
                    new_data = pandas.DataFrame(this_collector.data)
                    data = pandas.concat([data, new_data])

        each_benchmark.after_all()

    data = data.reset_index()

    filename = config.test_name
    if config.formatter_modes:
        for mode in config.formatter_modes:
            this_formatter = formatter.formatter.Formatter.get_formatter(mode)
            converted_data = this_formatter.convert(data)
            print(type(converted_data))
            print(converted_data)
            this_formatter.save(filename, converted_data)

def run_with(*classes):
    """
        Hannah, what is this?
    """
    for c in classes:
        benchmark.benchmark.Benchmark.register_benchmark(c.__name__, c)
    run()

if __name__ == "__main__":
    run(args)
