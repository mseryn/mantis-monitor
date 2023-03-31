"""
This code is licensed under LGPL v 2.1
See LICENSE for details
Authored by hgreenbl
"""

#import logging
import mantis_monitor
import itertools
import subprocess
import os, sys

#logging.basicConfig(filename='testing.log', encoding='utf-8', format='%(levelname)s:%(message)s', level=logging.DEBUG)

#sys.path.append(os.getenv('LMOD_DIR') + '/../init')
#from env_modules_python import module
#module("use /lus/grand/projects/SEEr-planning/spack/share/spack/modules/linux-ubuntu20.04-zen2/")
#module("load openfoam-org-8-gcc-9.3.0-6taoysc")
#module("load conda/2021-11-30")

class AEFoam(mantis_monitor.benchmark.benchmark.Benchmark):
    cwd = '/lus/grand/projects/SEEr-planning/PythonFOAM/Solver_Examples/AEFoam/Run_Case'
    env = None # don't overwrite externally-set env vars

    @classmethod
    def generate_benchmarks(cls, arguments):
        return [cls({'gpu_count': gpu_count}) for gpu_count in arguments['gpu_counts']]

    def before_each(self):
        print(f'Starting run with {self.gpu_count} GPUs')
        os.putenv('CUDA_VISIBLE_DEVICES', ','.join(str(i) for i in range(self.gpu_count)))
        print('Cleaning output', flush=True)
        #subprocess.run('/lus/grand/projects/SEEr-planning/PythonFOAM/Solver_Examples/AEFoam/Run_Case/Allclean')
        #subprocess.run('blockMesh', shell=True)
        subprocess.run('rm *.h5', shell=True, cwd=self.cwd)
        subprocess.run("find . -maxdepth 1 -regex '\./\([1-9][0-9]*\|[0-9][0-9]*\.[0-9][0-9]*\)' -exec rm -r {} \;", shell=True, cwd=self.cwd)
        subprocess.run('rm -r processor*', shell=True, cwd=self.cwd)
        print('Decomposing mesh')
        subprocess.run('decomposePar', shell=True, cwd=self.cwd)

    def get_run_command(self):
        return f'mpiexec -np 2 ~/OpenFOAM/hgreenbl-8/platforms/linux64GccDPInt32-spack/bin/AEFoam -parallel -fileHandler collated'
        #return f'mpiexec -np 2 ~/OpenFOAM/hgreenbl-8/platforms/linux64GccDPInt32-spack/bin/AEFoam -parallel'
        #return f'~/OpenFOAM/hgreenbl-8/platforms/linux64GccDPInt32-spack/bin/AEFoam'

    def __init__(self, arguments):
        self.gpu_count = arguments['gpu_count']
        self.name = f'AEFoam_{self.gpu_count}'

mantis_monitor.monitor.run_with(AEFoam)

