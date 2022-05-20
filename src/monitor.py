import benchmark
import configuration
import collector
import formatter

import logging
import argparse
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
    config.print_all()

    run_benchmarks = []
    for manual_benchmark in config.contents["benchmarks"]:
        for name, runscript in manual_benchmark.items():
            run_benchmarks.append(benchmark.Benchmark(name = name, runscript = runscript[0]))
    


if __name__ == "__main__":
    run()
