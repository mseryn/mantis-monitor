# This file is part of the Mantis-Monitor data collection suite.
# Mantis, including the data collection suite (mantis-monitor) and is

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
This file contains the implementation of the Nvidia Collector.

The Nvidia Collector can take many forms and use several tools:
- NVIDIA-smi
- nvprof
- ncu

This Collector is a good example of leveraging different TestRun()
implementations to achieve different monitoring tasks.
"""

#import logging
import math
import subprocess
import asyncio
import os
import os.path
import csv
import copy
import datetime

import pprint
import pandas

from mantis_monitor.collector.collector import Collector

#logging.basicConfig(filename='testing.log', encoding='utf-8', \
#    format='%(levelname)s:%(message)s', level=logging.DEBUG)

class NvidiaCollector(Collector):
    """
    This is the implementation of the base NVIDIA Collector.

    It inherits directly from the Collector() class.

    :ivar name: NvidiaCollector
    :ivar description: Describes this collector
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar configuration: Configuration object from this mantis-monitor instance
    :ivar testruns: List of TestRun() instances to run against this Collector
    :ivar data: Data from this Collector instance stored in the UDF

    :ivar modes: Which metrics to collect, comes from Configuration()
    :ivar gen: The SM value on the system, comes from Configuration()
    :ivar global_id: An int used to uniquely identify each TestRun()
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    """
    def __init__(self, configuration, iteration, benchmark, benchmark_set):
        """
        Init the object
        Run setup

        :param configuration: Configuration object from this mantis-monitor instance
        :type configuration: Configuration()
        :param iteration: The current experimental iteration
        :type iteration: int
        :param benchmark: Benchmark class this Collector is initiated against
        :type benchmark: Benchmark()
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :type benchmark_set: str

        :return: None
        """
        self.name = "NvidiaCollector"
        self.description = "Collector for configuring nvidia profiling metric collection"
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.iteration = iteration

        self.modes = configuration.collector_modes["nvidia"]["modes"]
        self.gen = configuration.collector_modes["nvidia"]["gen"]

        self.timescale = configuration.timescale # note this needs to be ms, same as configuration file
        self.testruns = []
        self.filename = "{testname}-iteration_{iter_count}-benchmark_{benchstring}-set_{benchsetstring}-nvidia_{{nvidia_identifier}}".format(testname = configuration.test_name, \
            iter_count = iteration, benchstring = benchmark.name, benchsetstring = self.benchmark_set)
        self.data = []
        self.global_ID = 0

        self.setup()


    def setup(self):
        """
        Sets up all SMIOverTimeTestRun() and NsysTestRun() instances to collect 
        all counters and metrics

        Attempts to abstract away from the user what values are needed

        Currently supported modes include:
        - power_time
        - utilization_time
        - memory_basic_time
        - temperature_time
        - clocks_time

        TODO:
        - Extend backward to use nvprof based on SM version
        - Overlap modes that can co-collect
        - Embrace the NVP datatype

        :return: None
        """

        if "power_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "power_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaPowerTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["power.draw"], "time, W", self.benchmark_set))
        if "utilization_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "utilization_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaUtilizationTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["utilization.gpu","utilization.memory"], "time, pct", self.benchmark_set))
        if "memory_basic_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "memory_basic_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaMemoryBasicTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["memory.total", "memory.used", "memory.free"], "time, GB", self.benchmark_set))
        if "temperature_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "temperature_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaTemperatureTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["temperature.gpu","temperature.memory"], "time, C", self.benchmark_set))
        if "clocks_time" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "clocks_time")
            self.testruns.append(SMIOverTimeTestRun("NvidiaClocksTime", self.benchmark, current_filename, self.iteration, self.timescale, \
                ["clocks.current.graphics","clocks.current.sm", "clocks.current.memory", "clocks.current.video"], "time, clocks", self.benchmark_set))
        if "gpu_trace" in self.modes:
            current_filename = self.filename.format(nvidia_identifier = "gpu_trace")
            self.testruns.append(NsysTestRun("NvidiaGPUTrace", self.timescale, self.benchmark, current_filename, self.iteration, self.benchmark_set))

    async def run_all(self):
        """
        Runs all TestRun() instances for this Benchmark()

        :return: None, yielded for each invocation of the Benchmark associated
        with this Collector instance
        """
        for this_testrun in self.testruns:
            this_testrun.benchmark.before_each()
            data = await this_testrun.run()
            this_testrun.benchmark.after_each()
            if isinstance(data, list):
                self.data.extend(data)
            else:
                self.data.append(data)
            yield

class SMIOverTimeTestRun():
    """
    Encapsulates each individual call to NVIDIA smi over time

    :ivar name: This TestRun()'s unique name (using global_id)
    :ivar measurements: The list of metrics to collect
    :ivar units: The units of the measurements
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar data: The data collected during this instance of NVIDIA smi
    :ivar duration: The duration which this instance of NVIDIA smi ran for

    The format of stored data is as follows (in a dictionary):
    - "benchmark_name": self.benchmark.name,
    - "benchmark_set":  self.benchmark_set,
    - "collector_name": self.name,
    - "iteration":      self.iteration,
    - "timescale":      self.timescale,
    - "units":          "count per timescale milliseconds",
    - "measurements":   self.counters,
    - "duration":       0,
    """
    def __init__(self, name, benchmark, filename, iteration, timescale, measurements, units, benchmark_set):
        """
        Init this TestRun()

        :param name: This TestRun()'s unique name (using global_id)
        :param measurements: The list of metrics to collect
        :param units: The units of the measurements
        :param timescale: The time between collections in MS, comes from Configuration()
        :param filename: A unique filename to use for intermediate data storage
        :param benchmark: Benchmark class this Collector is initiated against
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :param iteration: The statistical or experimental iteration

        :return: None
        """
        self.name = name
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.filename = filename
        self.iteration = iteration
        self.timescale = timescale
        self.measurements = measurements
        self.units = units
        self.duration = 0

        measurements_string = ",".join(self.measurements)
        self.smi_runstring = "nvidia-smi --query-gpu=timestamp,index,{measure} --loop-ms=1000 --format=csv,noheader,nounits"
        self.smi_runcommand = self.smi_runstring.format(filename = self.filename, measure = measurements_string)
        self.bench_runcommand = self.benchmark.get_run_command()
        self.data = {   "benchmark_name":   self.benchmark.name, \
                        "benchmark_set":    self.benchmark_set, \
                        "collector_name":   self.name, \
                        "iteration":        self.iteration, \
                        "timescale":        self.timescale, \
                        "units":            self.units, \
                        "measurements":     self.measurements, \
                        "duration":         self.duration, \
                        }

    # TODO (zcornelius): Fix SMI to use as a process wrapper here, instead of system-wide
    async def run(self):
        """
        Call this to run this instance of NVIDIA SMI
        """

        # Run it

        # Start SMI
        smi_filename = "smi_data.csv"
        smi_data = open(smi_filename, "w")
        smi_proc = subprocess.Popen(self.smi_runcommand.split(" "), stdout = smi_data)

        # Run benchmark
        print('Running command ' + self.bench_runcommand)
        starttime = datetime.datetime.now()
        process = await asyncio.create_subprocess_shell(self.bench_runcommand, cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()
        # Old subprocess mechanism
        # process = subprocess.run(self.bench_runcommand, shell=True, executable="/bin/bash", cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()

        # Kill SMI
        smi_proc.kill()
        smi_data.close()

        # Collect data
        gpu_indices = set()
        with open(smi_filename, 'r') as csvfile:
            for line in csvfile:
                line = line.strip().split(",")
                if len(line) > 1:
                    time = line[0]
                    gpu_index = line[1].strip()
                    gpu_indices.add(gpu_index)
                    for i, measurement in enumerate(self.measurements):
                        key = "gpu_{index}_{measurement}".format(index = gpu_index, measurement = measurement)
                        self.data.setdefault(key, []).append([time, float(line[i+2].strip())])

        # Clean up files
        os.remove(smi_filename)

        self.duration = (endtime - starttime).total_seconds()
        self.data["duration"] = self.duration

        return self.data


class NsysTestRun():
    """
    This is the implementation of the nsys gpu trace testrun

    GPU tracing produces lots of data and many options. This implementation
    collects summary metrics over several categories of data:

    - cuda_api_summary
    - dx12_gpu_marker_summary
    - dx11pixsum
    - gpu_kernel_summary
    - gpu_mem_size_summary
    - gpu_mem_time_summary
    - khr_debug_pu_summary
    - khr_debug_summary
    - nvtx_summary
    - openmp_summary
    - os_runtime_summary
    - pixel_summary
    - vulkan_gpu_marker_summary
    - vulkan_marker_summary

    :ivar name: This TestRun()'s unique name (using global_id)
    :ivar timescale: The time between collections in MS, comes from Configuration()
    :ivar filename: A unique filename to use for intermediate data storage
    :ivar benchmark: Benchmark class this Collector is initiated against
    :ivar benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
    :ivar iteration: The statistical or experimental iteration
    :ivar data: The data collected during this instance of NVIDIA smi
    :ivar duration: The duration which this instance of NVIDIA smi ran for
    :ivar runstring: The command to run gpu tracing using nsys
    :ivar parsestring: The command to digest data from gpu tracing through nsys
    :ivar runcommand: The full command with inserted Benchmark() run information

    The format of stored data is as follows (in a dictionary):
    - "benchmark_name": self.benchmark.name,
    - "benchmark_set":  self.benchmark_set,
    - "collector_name": self.name,
    - "iteration":      self.iteration,
    - "timescale":      self.timescale,
    - "units":          "count per timescale milliseconds",
    - "measurements":   self.counters,
    - "duration":       0,
    """
    def __init__(self, name, timescale, benchmark, filename, iteration, benchmark_set):
        """
        Init this TestRun()

        :param name: This TestRun()'s unique name (using global_id)
        :param timescale: The time between collections in MS, comes from Configuration()
        :param filename: A unique filename to use for intermediate data storage
        :param benchmark: Benchmark class this Collector is initiated against
        :param benchmark_set: Colon-seprated list of benchmarks co-running with the benchmark
        :param iteration: The statistical or experimental iteration

        :return: None
        """
        self.name = name
        self.timescale = timescale
        self.benchmark = benchmark
        self.benchmark_set = benchmark_set
        self.filename = os.path.join(os.getcwd(), filename)
        self.iteration = iteration
        self.runstring = "nsys profile --force-overwrite=true --gpu-metrics-device=all -o {filename} {runcommand}"
        self.parsestring = "nsys stats --force-overwrite=true --format csv {filename}.{{suffix}} -o {filename}".format(filename = self.filename)
        self.duration = 0

        self.bench_runcommand = self.benchmark.get_run_command()
        self.runcommand = self.runstring.format(filename = self.filename, runcommand = self.bench_runcommand)
        self.data = []
        self.data_prototype = {
            "benchmark_name": self.benchmark.name,
            "benchmark_set":  self.benchmark_set,
            "collector_name": self.name,
            "iteration":      self.iteration,
            "timescale":      self.timescale,
            "units":          "summary statistics",
            "measurements":   [],
            "duration":       0,
        }



    async def run(self):
        """
        Call this to run this instance of NVIDIA nsys using GPU trace mode

        Currently attempts to collect:
        - cuda_api_summary
        - dx12_gpu_marker_summary
        - dx11pixsum
        - gpu_kernel_summary
        - gpu_mem_size_summary
        - gpu_mem_time_summary
        - khr_debug_pu_summary
        - khr_debug_summary
        - nvtx_summary
        - openmp_summary
        - os_runtime_summary
        - pixel_summary
        - vulkan_gpu_marker_summary
        - vulkan_marker_summary

        Anything that doesn't produce files is ignored.
        """
        files_to_names = {"cudaapisum.csv" : "cuda_api_summary", \
                               "dx12gpumarkersum.csv": "dx12_gpu_marker_summary", \
                               "dx11pixsum.csv": "dx11pixsum", \
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
        starttime = datetime.datetime.now()
        process = await asyncio.create_subprocess_shell(self.runcommand, cwd=self.benchmark.cwd, env=self.benchmark.env)
        await process.wait()
        # process = subprocess.run(self.runcommand, shell=True, executable="/bin/bash", cwd=self.benchmark.cwd, env=self.benchmark.env)
        endtime = datetime.datetime.now()
        duration = (endtime - starttime).total_seconds()

        # Gather data
        parsestring_suffix = "placeholder-should-change"
        if os.path.isfile(".".join([self.filename, "qdrep"])):
            parsestring_suffix = "qdrep"
        elif os.path.isfile(".".join([self.filename, "nsys-rep"])):
            parsestring_suffix = "nsys-rep"
        self.parsestring = self.parsestring.format(suffix = parsestring_suffix)
        process = subprocess.run(self.parsestring, shell=True, cwd=self.benchmark.cwd)

        # Collect data
        # We will go through every possible collection mode and store it only if it contains data
        cwd_path_component = self.benchmark.cwd or ''
        for filename_suffix, contents_name in files_to_names.items():
            filename = os.path.join(cwd_path_component, "{filename_prefix}_{filename_suffix}".format(filename_prefix = self.filename, filename_suffix = filename_suffix))
            sub_data = []
            data_copy = copy.deepcopy(self.data_prototype)
            if os.path.isfile(filename):
                with open(filename, 'r') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        sub_data.append(row)
                # Clean up files
                os.remove(filename)

            if len(sub_data) > 1:
                data_copy["measurements"].append(contents_name)
                data_copy["duration"] = duration
                data_copy[contents_name] = sub_data

                self.data.append(data_copy)

#        os.remove("{}.qdrep".format(os.path.join(cwd_path_component, self.filename)))
        os.remove("{}.sqlite".format(os.path.join(cwd_path_component, self.filename)))


        return self.data


Collector.register_collector("nvidia", NvidiaCollector)
