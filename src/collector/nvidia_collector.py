"""
Implementation of Mantis nvidia SMI collector

Author: Melanie Cornelius
This code is licensed under LGPL v 2.1
See LICENSE for details
"""

#import logging
import math
import subprocess
import os
import csv
import copy

import pprint
import pandas

from collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class NvidiaCollector(Collector):
    """
    This is the implementation of the nvidia tool data collector
    """
    
    def __init__(self, configuration, iteration, benchmark):
        self.name = "NvidiaCollector"
        self.description = "Collector for configuring nvidia profiling metric collection"
        self.benchmark = benchmark
        self.iteration = iteration

        self.modes = configuration.collector_modes["nvidia"]["modes"]
        self.gen = configuration.collector_modes["nvidia"]["gen"]

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-nvidia_{{nvidia_identifier}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name)
        self.data = []
        self.global_ID = 0

        self.setup()


    def setup(self):
        if "power_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "power_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaPowerTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["power.draw"], "time, W"))
        if "utilization_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "utilization_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaUtilizationTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["utilization.gpu","utilization.memory"], "time, pct"))
        if "memory_basic_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "memory_basic_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaMemoryBasicTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["memory.total", "memory.used", "memory.free"], "time, GB"))
        if "temperature_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "temperature_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaTemperatureTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["temperature.gpu","temperature.memory"], "time, C"))
        if "clocks_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "clocks_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaClocksTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["clocks.current.graphics","clocks.current.sm", "clocks.current.memory", "clocks.current.video"], "time, clocks"))
        if "gpu_trace" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "gpu_trace")
            self.testruns.append(NsysTestRun("NvidiaGPUTrace", self.timescale, self.benchmark, current_filename, self.iteration))

        # add more here as more modes supported
        """
                 13       - power_time
         14       - utilization_time
         15       - memory_basic_time
         16       - temperature_time
         17       - clocks_time
        """

    def run_all(self):
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = this_testrun.run()
            this_testrun.benchmark.after_each()
            if isinstance(data, list):
                self.data.extend(data)
            else:
                self.data.append(data)

class SMIOverTimeTestRun():
    """
    This is the generic SMI implementation to collect measurements over time
    """
    def __init__(self, name, benchmark, filename, iteration, timescale, measurements_list, units):
        self.name = name
        self.benchmark = benchmark
        self.filename = filename
        self.iteration = iteration
        self.timescale = timescale
        self.measurements_list = measurements_list
        self.measurements = {}
        self.units = units
        index = 2
        for measurement in measurements_list:
            self.measurements[measurement] = index
            index = index + 1

        measurements_string = ",".join(list(self.measurements.keys()))
        self.smi_runstring = "nvidia-smi --query-gpu=timestamp,index,{measure} --loop-ms=1000 --format=csv"
        self.smi_runcommand = self.smi_runstring.format(filename = self.filename, measure = measurements_string)
        self.bench_runcommand = self.benchmark.get_run_command()
        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "units":            self.units, \
                        "measurements":     self.measurements_list, \
                        }

    def run(self):
        # Run it

        # Start SMI
        smi_filename = "smi_data.csv"
        smi_data = open(smi_filename, "w")
        smi_proc = subprocess.Popen(self.smi_runcommand.split(" "), stdout = smi_data)

        # Run benchmark
        discarded_output = subprocess.run(self.bench_runcommand.split(" "), capture_output=True)

        # Kill SMI
        smi_proc.kill()
        smi_data.close()
        
        # Determine number of GPUs measured
        gpu_indices = []
        first = True
        with open(smi_filename, 'r') as csvfile:
            for line in csvfile:
                line = line.strip().split(",")
                if len(line) > 1 and not first:
                    gpu_index = line[1].strip()
                    if gpu_index not in gpu_indices:
                        gpu_indices.append(gpu_index)
                    else:
                        break
                if first:
                    first = False

        # Add metadata to measurements column as well as empty data columns
        for gpu_index in gpu_indices:
            for measurement in self.measurements.keys():
                keyname = "gpu_{index}_{measurement}".format(index = gpu_index, measurement = measurement)
                self.data[keyname] = []

        # Collect data
        first = True
        with open(smi_filename, 'r') as csvfile:
            for line in csvfile:
                line = line.strip().split(",")
                if len(line) > 1 and not first:
                    time = line[0]
                    gpu_index = line[1].strip()
                    for measurement_name, measurement_index in self.measurements.items():
                        measurement_value = float(line[measurement_index].split()[0].strip())
                        keyname = "gpu_{index}_{measurement}".format(index = gpu_index, measurement = measurement_name)
                        self.data[keyname].append((time, measurement_value))
                if first:
                    first = False

        # Clean up files
        os.remove(smi_filename)

        return self.data


class NsysTestRun():
    """
    This is the implementation of the nsys gpu trace testrun
    """
    def __init__(self, name, timescale, benchmark, filename, iteration):
        self.name = name
        self.timescale = timescale
        self.benchmark = benchmark
        self.filename = filename
        self.iteration = iteration
        self.runstring = "nsys profile --gpu-metrics-device=all -o {filename} {runcommand}"
        self.parsestring = "nsys stats --format csv small_test-iteration_0-benchmark_XSBench_cuda-nvidia_gpu_trace.qdrep -o {}".format(self.filename)
        self.runcommand = self.runstring.format(filename = self.filename, runcommand = self.benchmark.get_run_command())
        self.data = []
        self.data_prototype = {
            "benchmark_name": self.benchmark.name,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "timescale":      self.timescale,
            "units":          "summary statistics",
            "measurements":   [],
        }


    def run(self):
        files_to_names = {"cudaapisum.csv" : "cuda_api_summary", \
                               "dx12gpumarkersum.csv": "dx12_gpu_marker_summary", \
                               "gpukernsum.csv": "gpu_kernel_summary", \
                               "gpumemsizesum.csv": "gpu_mem_size_summary", \
                               "gpumemtimesum.csv": "gpu_mem_time_summary", \
                               "khrdebuggpusum.csv": "khr_debug_pu_summary", \
                               "khrdebugsum.csv": "khr_debug_summary", \
                               "nvtxsum.csv": "nvtx_summary", \
                               "openmpevtsum.csv": "openmp_summary", \
                               "osrtsum.csv": "os_runtime_summary", \
                               "pixsum.csv": "pixel_summary", \
                               "vulkangpumarkersum.csv": "vulkan_gpu_marker_summary", \
                               "vulkanmarkerssum.csv": "vulkan_marker_summary", \
                               }
        # Run it

        runcommand_parts = self.runcommand.split(" ")
        output = subprocess.run(runcommand_parts, capture_output=True, text=True)

        # Gather data
        parsecommand_parts = self.parsestring.split(" ")
        output = subprocess.run(parsecommand_parts, capture_output=True, text=True)

        # Collect data
        # We will go through every possible collection mode and store it only if it contains data
        for filename_suffix, contents_name in files_to_names.items():
            filename = "{filename_prefix}_{filename_suffix}".format(filename_prefix = self.filename, filename_suffix = filename_suffix)
            sub_data = []
            data_copy = copy.deepcopy(self.data_prototype)
            with open(filename, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    sub_data.append(row)

            if len(sub_data) > 1:
                data_copy["measurements"].append(contents_name)
                data_copy[contents_name] = sub_data

                self.data.append(data_copy)
            # Clean up files
            os.remove(filename)

        os.remove("{}.qdrep".format(self.filename))
        os.remove("{}.sqlite".format(self.filename))

        return self.data


Collector.register_collector("nvidia", NvidiaCollector)
