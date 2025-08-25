# Mantis: Unified Performance Monitoring for HPC

**Mantis** is an open-source Python toolkit that streamlines performance monitoring and profiling in high-performance computing (HPC) environments. It wraps and unifies diverse monitoring tools to deliver a consistent, user-friendly experience—empowering researchers and developers to collect, analyze, and compare application performance across heterogeneous systems with ease.

For full documentation, please visit [the wiki](https://github.com/mseryn/mantis-monitor/wiki).

---

## Why Mantis?

Performance monitoring is essential in HPC, but it’s often complex, fragmented, and error-prone. Existing tools are powerful—but inconsistent in interfaces, output formats, and usage constraints. Mantis addresses this challenge by:

- Operating entirely in user space—no root, kernel modules, or system hooks required.
- Using a single, structured YAML configuration file to define monitoring tasks.
- 🛠Orchestrating a wide range of profiling and monitoring tools behind the scenes.
- Producing unified, analysis-ready outputs in structured formats like JSON, CSV, Parquet, and Pandas.
- Enabling repeatable and portable performance experiments across HPC environments.

---

## Key Features

- **Unified Tool Integration**  
  Seamlessly wraps heterogeneous profiling and monitoring tools:
  - Linux `perf`, `/proc`, `time`
  - GPU profilers (`nvprof`, `ncu`, `rocprof`, `nvidia-smi`, `amd-smi`)
  - Facility-level metrics (IPMI, energy sensors, etc.)

- **Consistent Data Output**  
  All tools report into a standardized, extensible schema compatible with flat (CSV/XML) and rich (JSON/Parquet/Pandas) formats.

- **No Code Modifications**  
  Mantis runs alongside your applications—no source code changes, instrumentation, or recompilation required.

- **Modular and Extensible**  
  Clean object-oriented design makes it easy to plug in new tools or output formats with minimal boilerplate.

- **Portable and Lightweight**  
  Runs on local systems, clusters, and supercomputers with no site-specific dependencies.

- **Research-Ready**  
  Replace fragile bash pipelines with reproducible YAML configurations and structured outputs.

---

## Supported Tools

Mantis supports a wide variety of profiling and monitoring tools, including but not limited to:

### **CPU and System**
- Linux `perf`
- `/proc` virtual filesystem

### **GPU**
- NVIDIA: `nvidia-smi`, `nvprof`, Nsight Compute (`ncu`)
- AMD: `amd-smi`, `rocprof`, uProf

### **Power and Platform**
- IPMI (node-level energy, thermals, fans)
- Facility tools (e.g., HPCM support in progress)

### **Other**
- Time-to-completion collectors
- Environment and runtime metadata

See the [documentation](https://github.com/mseryn/mantis-monitor/wiki) for a full list and configuration examples.

---

## Architecture

Mantis follows a clean, modular design to ensure extensibility and transparency:

- **Configuration**  
  All experiments are described in YAML, specifying target programs, monitoring tools, environment variables, and output preferences.

- **Benchmark Module**  
  Launches target applications with precise control over environment and inputs.

- **Collector Module**  
  Coordinates profiling tools and captures their outputs.

- **Formatter Module**  
  Normalizes and exports collected data into user-friendly formats for downstream analysis.

---

## The Unified Data Schema (UDS)

At the core of Mantis is its **Unified Data Schema (UDS)**: a structured, extensible format that abstracts and unifies metrics from all supported tools.

The UDS is:

- Tool-agnostic
- Compatible with flat and nested formats
- Easily queryable using standard Python libraries or SQL
- Designed for merging, comparison, and statistical analysis

See the [Unified Data Schema documentation](https://github.com/mseryn/mantis-monitor/wiki/Unified-Data-Schema) for schema structure and usage examples.

---

## Documentation & Resources

- **Full Documentation**  
  https://github.com/mseryn/mantis-monitor/wiki

- **YAML Configuration Examples**  
  [Sample configs](https://github.com/mseryn/mantis-monitor/wiki/Configuration-Examples)

- **Extending Mantis**  
  [Developer Guide](https://github.com/mseryn/mantis-monitor/wiki/Extending-Mantis)

- **Unified Data Schema (UDS)**  
  [Schema Reference](https://github.com/mseryn/mantis-monitor/wiki/Unified-Data-Schema)

---

## License

Mantis is released under the **GNU Lesser General Public License (LGPL v3)**. See the [LICENSE](LICENSE) file for details.

---

## Citation

If you use Mantis in your research or publications, please cite:

> [CITATION GOES HERE – add BibTeX or DOI]

