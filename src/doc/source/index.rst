Welcome to the docs for mantis-monitor
======================================

mantis-monitor is a system to simlpify program monitoring and data collection. 

The intents of Mantis are as follows:
- Use many monitoring tools from one invocation
- Run many codes and variations on codes from one invocation
- Recieve all data in one schema
- Make it easy to extend the framework to include new monitoring tools and output to new data formats

Mantis requires **no code changes** and **minimal user configuration** for use.
All data is output to the user **in a single file and single schema** regardless of the monitoring tool used.
Further, Mantis uses **standard, off-the-shelf** monitoring tools and is easily extended to support more.
Mantis leverages *standard OO design* and is easily extended to cover changing research concerns.

This file is part of the Mantis data collection suite. Mantis, including the data collection suite (mantis-monitor) and the dashboard (mantis-dash) are copyright (C) 2016-2023 by Melanie Cornelius.

**Mantis is free software**: you can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Mantis is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with Mantis. If not, see https://www.gnu.org/licenses/.

---

This repo has a `permanent home <https://github.com/mseryn/mantis-monitor>`_.

Any other location might be out-of-date

---

Special thanks to contributors zcorneli and hgreenbl


.. note::

   This project is under active development and is supported in part by US National Science Foundation grants CCF-2119294.

Contents
--------

.. toctree::

   Home <self>
   getting_started
   config_walkthrough
   api
