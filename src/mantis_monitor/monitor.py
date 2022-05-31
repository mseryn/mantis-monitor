from mantis_monitor import benchmark
from mantis_monitor import configuration
from mantis_monitor import collector
from mantis_monitor import formatter

import pandas
#import logging
import argparse
import pprint
import sys
#import testrun


#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

def run(argv=sys.argv):
    """
    Main run script for Mantis Monitor
    """
    config_location = None
    if len(argv) > 1:
        config_location = argv[1]
    else:
        #logging.warning("No config file provided; running with no-op test benchmark")
        print("MUST PROVIDE CONFIG FILE AT RUNTIME or default is used")
    config = configuration.Configuration(location=config_location)
    config.print_all()

    all_dataframes = []
    dataframe_columns = ["benchmark_name", "collector_name", "iteration", "timescale", "units", "measurements"]
    data = pandas.DataFrame(columns = dataframe_columns)

    run_benchmarks = []
    for name, arguments in config.contents["benchmarks"].items():
        run_benchmarks.extend(benchmark.benchmark.Benchmark.get_benchmarks(name, arguments))

    # TODO should move iterations into collector? What about statistics? Hold off for now.

    run_collectors = []
    for each_benchmark in run_benchmarks:

        each_benchmark.before_all()

        for iteration in range(0, config.iterations):
            # TODO generalize this once format consistent
            for mode in config.collector_modes:
                if "perf" in mode:
                    this_collector = collector.collector.Collector.get_collector(mode, config, iteration, each_benchmark)
                    this_collector.run_all()
                    new_data = pandas.DataFrame(this_collector.data)
                    data = pandas.concat([data, new_data])
                if "nvidia" in mode:
                    this_collector = collector.collector.Collector.get_collector(mode, config, iteration, each_benchmark)
                    this_collector.run_all()
                    new_data = pandas.DataFrame(this_collector.data)
                    data = pandas.concat([data, new_data])

        each_benchmark.after_all()


    filename = config.test_name
    if config.formatter_modes:
        for mode in config.formatter_modes:
            this_formatter = formatter.formatter.Formatter.get_formatter(mode)
            converted_data = this_formatter.convert(data)
            this_formatter.save(filename, converted_data)

if __name__ == "__main__":
    run()
