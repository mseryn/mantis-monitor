"""
Module to handle all components configuring Mantis Monitor

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

import pprint
import logging
import yaml
import subprocess
import os

#TODO how do I make sure all the logs go to the same place? Just reuse the name?
logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Configuration:
    """
    Outer-most object to control Configuration elements
    """
    def __init__(self, location="../config.yaml", generate_new_yaml=False):
        """The config file used during this invocation of mantis-monitor"""
        self.location = location
        """Config file location, a string"""
        if os.path.exists(self.location) and not generate_new_yaml:
            self.contents = yaml.load(open(self.location))
            logging.info("read yaml file at %s", self.location)
        else:
            self.contents = generate_yaml()
            with open(self.location, 'w') as yamlfile:
                yaml.dump(self.contents, yamlfile)
                logging.info("Dumped new yaml file at %s", self.location)

        self.set_all_contents()
        check_perf()
        check_nvidia()

    def set_all_contents(self):
        self.collector_modes = self.contents["collection_modes"]
        self.benchmarks = self.contents["benchmarks"]
        self.formatter_modes = self.contents["formatter_modes"]
        self.memory_modes = self.contents["memory_modes"]
        self.nvidia_modes = self.contents["nvidia_modes"]
        self.perf_counters = self.contents["perf_counters"]

        # This is needed for advanced benchmarks self.benchmark_configurations = self.contents["benchmark_configurations"]

        self.debug_mode = self.contents["debug"]
        self.log = self.contents["log"]

        self.test_name = self.contents["test_name"]
        self.iterations = self.contents["iterations"]
        self.timescale = self.contents["time_count"]
        self.pmu_count = self.contents["pmu_count"]

    def print_all(self):
        pprint.pprint(self.contents)


def generate_yaml():
    """Helper function to generate a new default yaml configuration file
    """
    # Get possible perf counters and search for default counters
    perf_counters = get_available_perf()
    selected_counters = closest_match(perf_counters)

    # Build default yaml
    default_yaml = {
        'test_name': 'DEFAULT', 
        'debug': True, 
        'log': True, 
        'iterations': 2, 
        'perf_counters': selected_counters,
        'nvidia_modes': ['api_trace', 'gpu_trace', 'power_over_time'], 
        'memory_modes': ['high_watermark', 'memory_over_time'], 
        'benchmarks': [{'XSBench': "./run script and args goes here"}, {'RSBench': "run script and args go here"}], 
        'pmu_count': 4, 'time_count': 100, 
        'formatter_modes': ['CSV']
    }

    return default_yaml


def closest_match(all_counters):
    """Function to do string closest-matching on perf counter names
    Early implementation should ignore case
    Add more match strings here for better fuzzy matching on new architectures
    If this becomes unweildy or enormous, move to fuzzy string matching, but it would be overkill
    in the current implementation
    """
    match_strings = {
        "instructions": ["instructions"],
        "cycles": ["cycles", "cpu-cycles"],
        "LLC stores": ["LLC-stores"],
        "page faults": ["page-faults"],
        "major faults": ["major-faults"],
        "memory BW": ["DRAM_BW_Use"],
        "cpu power": ["Average_Frequency"],
        "cpu utilization": ["CPU_Utilization"],
    }

    matched_counters = []
    for match_string_category, match_string_list in match_strings.items():
        # Want to ensure we only add a matched string once per category and once per
        # matching against that category, hence the use of the below temp variable
        # This is relatively inefficient, but for a small number of default values,
        # it should not be too expensive, only about 1,000 string match operations
        matched_counter_string = None
        for match_string in match_string_list:
            for counter_string in all_counters:
                if match_string.lower() == counter_string.lower():
                    matched_counter_string = counter_string

        if matched_counter_string:
            matched_counters.append(matched_counter_string)

    return matched_counters


def check_perf():
    perf_overall = subprocess.run("perf", capture_output=True)
    if not perf_overall:
        logging.info("Uh-oh, it looks like there's an issue using perf!")
    else:
        logging.info("Perf outputs")

def get_available_perf():
    """Helper function to query perf and return all available counters
    """
    perf_list_raw = subprocess.run(["perf", "list", "--no-desc"], capture_output=True)
    raw_perf = str(perf_list_raw.stdout)
    raw_perf = raw_perf.split("\\n")
    perf_options = set()
    for raw_substring in raw_perf:
        raw_substring = raw_substring.split("[")[0].strip()
        if '"' in raw_substring:
            raw_substring = raw_substring.split('"')[1].strip()
        if "OR" in raw_substring:
            raw_substring = raw_substring.split('OR')[0].strip()
        if raw_substring and ":" not in raw_substring:
            perf_options.add(raw_substring)

    perf_options = list(perf_options)
    return perf_options

def check_nvidia():
    """Helper function to ensure nvidia systems function on this architecture, TODO
    """
    pass


if __name__ == "__main__":
    #c = Configuration(generate_new_yaml=True)
    c = Configuration()
    print(c.contents)
