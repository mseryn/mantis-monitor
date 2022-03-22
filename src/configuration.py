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

logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Configuration:
    """
    Outer-most object to control Configuration elements
    """
    def __init__(self, location="../config.yaml"):
        """The config file used during this invocation of mantis-monitor"""
        self.location = location
        """Config file location, a string"""
        self.contents = yaml.load(open(self.location))
        self.check_contents()

    def check_contents(self):
        """Helper function to check the yaml file contents"""
        pass

def generate_yaml():
    # Check for needed tools
    check_perf()
    check_nvidia()

    # Get possible perf counters and search for default counters
    perf_counters = get_available_perf()
    selected_counters = closest_match(perf_counters)

    # Build default yaml
    


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
        #TODO should I make my own errors?
        logging.info("Uh-oh, it looks like there's an issue using perf!")
    else:
        logging.info("Perf outputs")

def get_available_perf():
    # Getting possible perf counters using parsing on 'perf list'
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
    pass


if __name__ == "__main__":
    c = Configuration()
    print(c.contents)
    generate_yaml()
