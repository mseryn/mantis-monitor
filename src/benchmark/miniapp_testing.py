"""
Module containing Hunter's miniapp based off (put the link here)

This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
from benchmark.benchmark import Benchmark
import itertools
import subprocess

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

class MiniApp(Benchmark):
    @classmethod
    def generate_benchmarks(cls, arguments):
        return [
            cls({"size": size, "gpu_count": gpu_count})
            for size, gpu_count in itertools.product(arguments["sizes"], arguments["gpu_count"])
        ]   

    def before_each(self):
        setup_commands = []
        setup_commands.append("source /etc/profile.d/z00_lmod.sh")
        setup_commands.append("module load conda")
        setup_commands.append("conda activate")
#        setup_commands.append("source /home/hnegron/Documents/my_env/bin/activate")
        setup_commands.append("source /lus/grand/projects/SEEr-planning/miniapp_env/bin/activate")
        # TODO hunter ensure this correctly sets your subdirectory per size of benchmark
        #setup_commands.append("/lus/grand/projects/SEEr-planning/{subdirectory}/05_Simulation_ML/ML_PythonC++_Embedding/ThetaGPU/".format(subdirectory=self.size_dir)
        setup_commands.append("cd ~/miniapps/{subdirectory}/".format(subdirectory=self.size_dir))
        setup_commands.append("source setup.sh")
        for setupcommand in setup_commands:
            print(setupcommand)
            parts = setupcommand.split(" ")
            subprocess.run(parts)

    def get_run_command(self):
        # changes depending on gpu_count
        # format string with arg as parameter
        print("mpirun -np {gpu_count} ./app --device".format(gpu_count = self.gpu_count))
        return "mpirun -np {gpu_count} ./app --device".format(gpu_count = self.gpu_count)

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
        self.name = "MiniApp_{gpu_count}GPUs_size{size}".format(gpu_count = self.gpu_count, size = self.size)

#Benchmark.register_benchmark_from_arguments("MiniApp", MiniApp, cross_product=["sizes", "gpu_counts"])
Benchmark.register_benchmark("MiniApp", MiniApp)

