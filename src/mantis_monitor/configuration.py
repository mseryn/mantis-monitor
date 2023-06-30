# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is
# copyright (C) 2016-2023 by Melanie Cornelius.

# Mantis is free software:
# you can redistribute it and/or modify it under the terms of the GNU Lesser
# General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version.

# Mantis is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along
# with Mantis. If not, see <https://www.gnu.org/licenses/>.

"""
This file contains the implementation of the Configuration class in
mantis-monitor. Currently, there is only one form of the Configuration
class.

This object is responsible for translating the config.yaml into
meaningful objects from the rest of the mantis-monitor architecture.

There is MUCH to do to improve this file, the current form is
functional and flexible.
"""
import pprint
import yaml
import subprocess
import os

class Configuration:
    """
    Outer-most object to control Configuration elements

    If no config file is offered, a generated default configuration, using
    the TestBenchmark Benchmark and the Linux time tool, will be used and written
    in the current directory.

    :ivar location: The config.yaml file to use, passed as the first (and only)
    argument to mantis-monitor.
    :ivar contents: The config.yaml contents loaded from the given file
    :ivar collector_modes: Which collectors to use in which modes
    :ivar benchmarks: Which Benchmarks to run, either custom Benchmark classes
    or items handed to the config.yaml file to auto-config into GenericBenchmark classes.
    :ivar benchmark_matrix: If provided, these benchmarks will co-run.
    :ivar formatter_modes: Which Formatter classes to use for outputting final data
    :ivar log: Boolean controlling whether or not to log data
    :ivar test_name: String to use as the name for this set of Benchmarks, Collectors, and
    Formatters
    :ivar iterations: The number of times to repeat the entire combination of all Benchmarks
    and Collectors, used to get statistically relevant experimental data
    :ivar timescale: The ms used between each time step during measurements over time
    :ivar perf_counters: A list of string Linux perf tool counters to measure

    .. todo ::
        Logging is broken system-wide. The Logging module in Python broke, need to fix this.
    """
    def __init__(self, location=None):
        """
        Init the object.

        :param location: A string of the path to the config.yaml file to use
        """
        self.location = location
        if location and os.path.exists(location):
            self.contents = yaml.safe_load(open(location))
            #logging.info("Read config yaml at %s", location)
        elif location:
            #logging.error("A config file was provided but could not be found")
            raise ValueError("Config file not found")
        else:
            self.contents = generate_default_config()
            dump_default_config(self.contents)

        self.set_all_contents()
        check_perf()
        check_nvidia()

    def set_all_contents(self):
        """
        Using the contents from the .yaml file, populate instance variables
        with appropriate information.
        """
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
        """
        A simple helper function to pretty-print the contents of the
        config.yaml file
        """
        pprint.pprint(self.contents)


def generate_default_config():
    """
    Helper function to generate a new default configuration

    :return: A dict of the contents of a default .yaml file
    """

    # Build default yaml
    default_yaml = {
        'benchmarks': {
            'TestBench': {
                'waittimes': [1, 4, 8],
            },
        },
        'collection_modes': {
            'ttc': ''
        },
        'formatter_modes': ['PandasPickle', 'CSV'],
        'perf_counters': selected_counters,

        'iterations': 1,
        'time_count': 1000,
        'log': True,
        'test_name': 'GENERATEDDEFAULT',
    }

    return default_yaml

def get_default_counters(all_counters):
    """
    Function to do string closest-matching on perf counter names
    Early implementation should ignore case
    Add more match strings here for better fuzzy matching on new architectures
    If this becomes unwieldy or enormous, move to fuzzy string matching, but it would be overkill
    in the current implementation

    :return: a list of matched Perf counters

    .. todo ::
        Correct against system's perf counters
        Fuzzy match for spelling, similar counters, etc
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

def dump_default_yaml(config):
    """
    Saves a generated .yaml file to DEFAULT.yaml

    :param config: The config dict object to save
    :param location: The location at which to save this file
    """
    with open("DEFAULT.yaml", 'w') as yamlfile:
        yaml.dump(config, yamlfile)


def check_perf():
    """
    Checks if perf can be used on this system

    .. todo ::
        Need to also check if PERF_EVENT_PARANOID is appropriate for using perf stat
    """
    perf_overall = subprocess.run("perf", capture_output=True)
    if not perf_overall:
        pass
        print("You're using PERF, but it doesn't look like you can use this on this system")
    else:
        pass

def check_nvidia():
    """
    Helper function to ensure nvidia systems function on this architecture

    .. todo ::
        Need to do this
    """
    pass

if __name__ == "__main__":
    c = Configuration()
    print(c.contents)
