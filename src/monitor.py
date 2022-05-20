import benchmark
import configuration
import collector
import formatter

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
    #logging.log("config elements are:")
    #logging.log(config.print_all())


    all_data = []
    run_benchmarks = []
    for manual_benchmark in config.contents["benchmarks"]:
        for name, runscript in manual_benchmark.items():
            run_benchmarks.append(benchmark.Benchmark(name = name, runscript = runscript[0]))

    run_collectors = []
    for each_benchmark in run_benchmarks:
        for iteration in range(0, config.iterations):
            run_collectors.append(collector.PerfCollector(config, iteration, each_benchmark))

    for each_collector in run_collectors:
        each_collector.run_all()
        all_data.append(each_collector.data)
    

    for thing in all_data:
        pprint.pprint(thing)

if __name__ == "__main__":
    run()
