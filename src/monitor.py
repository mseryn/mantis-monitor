import benchmark
import configuration
import collector
import formatter

import pandas
import logging
import argparse
import pprint
#import testrun


logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

def run():
    """
    Main run script for Mantis Monitor
    """
    config = configuration.Configuration()

    all_dataframes = []
    dataframe_columns = ["benchmark_name", "collector_name", "iteration", "timescale", "units", "measurements"]
    data = pandas.DataFrame(columns = dataframe_columns)

    run_benchmarks = []
    for name, arguments in config.contents["benchmarks"].items():
        new_benchmarks = benchmark.benchmark.Benchmark.get_benchmark_class(arguments["runner"]).generate_benchmarks(arguments)
        run_benchmarks.extend(new_benchmarks)

    # TODO should move iterations into collector? What about statistics? Hold off for now.

    run_collectors = []
    for each_benchmark in run_benchmarks:

        each_benchmark.before_all()

        for iteration in range(0, config.iterations):
            # TODO remove this once more modes supported
            for mode in config.collector_modes:
                if "perf" in mode:
                    this_collector = collector.collector.Collector.get_collector(mode, config, iteration, each_benchmark)
                    this_collector.run_all()
                    data = pandas.concat([data, pandas.DataFrame(this_collector.data)])

        each_benchmark.after_all()

    filename = config.test_name
    if config.formatter_modes:
        for mode in config.formatter_modes:
            this_formatter = formatter.formatter.Formatter.get_formatter(mode)
            converted_data = this_formatter.convert(data)
            this_formatter.save(filename, converted_data)

if __name__ == "__main__":
    run()
