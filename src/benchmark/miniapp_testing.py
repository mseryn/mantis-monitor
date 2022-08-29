"""
Module containing Hunter's miniapp based off (put the link here)

This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
from benchmark.benchmark import Benchmark
import itertools
import subprocess
import os


def bracketed_split(string, delimiter, strip_brackets=False):
    """ Split a string by the delimiter unless it is inside brackets.
    e.g.
        list(bracketed_split('abc,(def,ghi),jkl', delimiter=',')) == ['abc', '(def,ghi)', 'jkl']
    """

    openers = '{'
    closers = '}'
    opener_to_closer = dict(zip(openers, closers))
    opening_bracket = dict()
    current_string = ''
    depth = 0
    for c in string:
        if c in openers:
            depth += 1
            opening_bracket[depth] = c
            if strip_brackets and depth == 1:
                continue
        elif c in closers:
            assert depth > 0, f"You exited more brackets that we have entered in string {string}"
            assert c == opener_to_closer[opening_bracket[depth]], f"Closing bracket {c} did not match opening bracket {opening_bracket[depth]} in string {string}"
            depth -= 1
            if strip_brackets and depth == 0:
                continue
        if depth == 0 and c == delimiter:
            yield current_string
            current_string = ''
        else:
            current_string += c
    assert depth == 0, f'You did not close all brackets in string {string}'
    yield current_string


#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class MiniApp(Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [
            cls({"size": size, "gpu_count": gpu_count})
            for size, gpu_count in itertools.product(arguments["sizes"], arguments["gpu_count"])
        ]

#    def before_each(self):
#        print('Setting env using command ' + self.env_command)
#        envout = subprocess.check_output(self.env_command + '; echo ========================; env -0', shell=True, executable="/bin/bash", encoding='UTF-8', cwd=self.cwd)
#        envout = envout.split('========================')[1].strip().strip('\0')
#        self.env = dict(list(line.split('=', 1) for line in bracketed_split(envout, '\0')))
#        subprocess.run('./setup.sh', shell=True, cwd=self.cwd, env=self.env)

    def get_run_command(self):
        # changes depending on gpu_count
        # format string with arg as parameter
        print("mpirun -np {gpu_count} app --device gpu".format(gpu_count = self.gpu_count))
        return "mpirun -np {gpu_count} app --device gpu".format(gpu_count = self.gpu_count)

    def __init__(self, arguments):
        # format string on name including size and gpu count
        #self.sizes = arguments["sizes"]
        #self.gpu_counts = arguments["gpu_counts"]
        self.size = arguments["size"]
        self.gpu_count = arguments["gpu_count"]

        #TODO hunter, replace these with the relevant subdirectory locations, see line 29 in setup above for use
        sizes_to_directories = {"A": "miniappA", \
                                "B": "miniappB", \
                                "C": "miniappC", \
                                "D": "miniappD", \
                                "E": "miniappE", \
                                "F": "miniappF", \
                                }

        self.size_dir = sizes_to_directories[self.size]
        #self.pre_command = "source /etc/profile.d/z00_lmod.sh; module load conda; conda activate; source /lus/grand/projects/SEEr-planning/miniapp_env/bin/activate; cd ~/miniapps/{subdirectory}/; ".format(subdirectory=self.size_dir)
        self.env_command = "module load conda; conda activate; source /lus/grand/projects/SEEr-planning/miniapp_env/bin/activate"
        self.env = None
        self.cwd = os.path.expanduser("~/miniapps/{subdirectory}/app_build/".format(subdirectory=self.size_dir))
        self.name = "MiniApp_{gpu_count}GPUs_size{size}".format(gpu_count = self.gpu_count, size = self.size)

#Benchmark.register_benchmark_from_arguments("MiniApp", MiniApp, cross_product=["sizes", "gpu_counts"])
Benchmark.register_benchmark("MiniApp", MiniApp)

