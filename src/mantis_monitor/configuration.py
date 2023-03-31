"""
This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and is copyright (C) 2016-2023 by Melanie Cornelius.

Mantis is free software: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""

import pprint
#import logging
import yaml
import subprocess
import os

#TODO how do I make sure all the logs go to the same place? Just reuse the name?
#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class Configuration:
    """
    Outer-most object to control Configuration elements
    """
    def __init__(self, location=None):
        """The config file used during this invocation of mantis-monitor"""
        self.location = location
        """Config file location, a string"""
        if location and os.path.exists(location):
            self.contents = yaml.safe_load(open(location))
            #logging.info("Read config yaml at %s", location)
        elif location:
            #logging.error("A config file was provided but could not be found")
            raise ValueError("Config file not found")
        else:
            self.contents = generate_default_config()

        self.set_all_contents()
        check_perf()
        check_nvidia()

    def set_all_contents(self):
        self.collector_modes = self.contents["collection_modes"]
        self.benchmarks = self.contents["benchmarks"]
        if "benchmark_matrix" in self.contents:
            self.benchmark_matrix = self.contents["benchmark_matrix"]
        else:
            self.benchmark_matrix = None
        self.formatter_modes = self.contents["formatter_modes"]

        self.log = self.contents["log"]

        self.test_name = self.contents["test_name"]
        self.iterations = self.contents["iterations"]
        self.timescale = self.contents["time_count"]

        #check_before_set = ["perf_counters"]
        #for check_key in check_before_set:
        #    if check_key in self.contents.keys():
        #        self.check_key = self.contents[check_key]
        if "perf_counters" in self.contents.keys():
            self.perf_counters = self.contents["perf_counters"]

    def print_all(self):
        pprint.pprint(self.contents)


def generate_default_config():
    """Helper function to generate a new default configuration
    """
    # Get possible perf counters and search for default counters
    selected_counters = get_default_counters(get_available_perf())

    # Build default yaml
    default_yaml = {
        'benchmarks': {
            'TestBench': {
                'waittimes': [1, 4, 8],
            },
        },
        'collection_modes': {
            'perf': {
                'pmu_count': 4,
            },
            #'memory': {
            #    'modes': ['high_watermark', 'memory_over_time'],
            #},
            #'nvidia': {
            #    'modes': ['api_trace', 'gpu_trace', 'power_over_time', 'power_summary'],
            #    'gen': 'sm_80',
            #},
        },
        'formatter_modes': ['PandasPickle', 'CSV'],
        'perf_counters': selected_counters,

        'iterations': 1,
        'time_count': 1000,
        'log': True,
        #'debug': True,
        'test_name': 'GENERATEDDEFAULT',
    }

    return default_yaml

def get_default_counters(all_counters):
    """Function to do string closest-matching on perf counter names
    Early implementation should ignore case
    Add more match strings here for better fuzzy matching on new architectures
    If this becomes unwieldy or enormous, move to fuzzy string matching, but it would be overkill
    in the current implementation
    """
    match_strings = {
        "instructions": ["instructions"],
        "cycles": ["cycles", "cpu-cycles"],
        "LLC stores": ["LLC-stores"],
        "page faults": ["page-faults"],
        "major faults": ["major-faults"],
        #"memory BW": ["DRAM_BW_Use"],
        #"cpu power": ["Average_Frequency"],
        #"cpu utilization": ["CPU_Utilization"],
    }

    all_counters_folded = {counter.casefold() : counter for counter in all_counters}
    matches = []
    for match_string_category, match_string_list in match_strings.items():
        for match_string in match_string_list:
            counter = all_counters_folded.get(match_string.casefold())
            if counter:
                matches.append(counter)
                break

    return matches

def dump_default_yaml(location):
    config = generate_default_config()
    with open(location, 'w') as yamlfile:
        yaml.dump(config, yamlfile)
        logging.info("Dumped new yaml file at %s", location)


def check_perf():
    perf_overall = subprocess.run("perf", capture_output=True)
    if not perf_overall:
        pass
        #logging.info("Uh-oh, it looks like there's an issue using perf!")
    else:
        pass
        #logging.info("Perf outputs")

def get_available_perf():
    """Helper function to query perf and return all available counters
    """
    perf_list_raw = subprocess.run(
        # get events only, exclude metrics (for now)
        ["perf", "list", "--raw-dump", "hw", "sw", "cache", "tracepoint", "pmu", "sdt"],
        capture_output=True, text=True)
    return set(perf_list_raw.stdout.split())

def check_nvidia():
    """Helper function to ensure nvidia systems function on this architecture, TODO
    """
    pass

if __name__ == "__main__":
    #dump_default_yaml("../config.yaml")
    c = Configuration()
    print(c.contents)
