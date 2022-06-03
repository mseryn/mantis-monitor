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
    # Intake configuration
    # Build or configure benchmarks
    # Have collectors make testruns
    # Configure formatter
    # Run

    config = configuration.Configuration()
#    config.print_all()
    #logging.log("config elements are:")
    #logging.log(config.print_all())

    all_dataframes = []
    dataframe_columns = ["benchmark_name", "collector_name", "iteration", "timescale", "units", "measurements"]
    data = pandas.DataFrame(columns = dataframe_columns)

    run_benchmarks = []
    for name, arguments in config.contents["benchmarks"].items():
        # Turn this into a generator TODO
        # Make sure future benchmarks return list-style (generation)
        run_benchmarks.append(benchmark.benchmark.Benchmark.get_benchmarks(arguments["runner"], arguments))

    # TODO should move iterations into collector? What about statistics? Hold off for now.

    run_collectors = []
    for each_benchmark in run_benchmarks:
        for iteration in range(0, config.iterations):
#            run_collectors.append(collector.PerfCollector(config, iteration, each_benchmark))
            # TODO remove this once more modes supported
            for mode in config.collector_modes:
                if "perf" in mode:
                    run_collectors.append(collector.collector.Collector.get_collector(mode, config, iteration, each_benchmark))

    for each_collector in run_collectors:
        each_collector.run_all()
        all_dataframes.append(pandas.DataFrame(each_collector.data))

    for dataframe in all_dataframes:
        data = pandas.concat([data, dataframe])

    filename = config.test_name
    if config.formatter_modes:
        for mode in config.formatter_modes:
            this_formatter = formatter.formatter.Formatter.get_formatter(mode)
            converted_data = this_formatter.convert(data)
            this_formatter.save(filename, converted_data)


    

if __name__ == "__main__":
    run()
