# PROS CLI - Grafana GUI Fork

[![Build Status](https://dev.azure.com/purdue-acm-sigbots/CLI/_apis/build/status/purduesigbots.pros-cli?branchName=develop)](https://dev.azure.com/purdue-acm-sigbots/CLI/_build/latest?definitionId=6&branchName=develop)

=======
## Info
This fork is used for connecting to the [Grafana plugin](https://github.com/BWHS-Robotics/pros-grafana), adding the new command ``pros gui``. After installation, more info on using this project can be found on the [PROS GUI template repository](https://github.com/BWHS-Robotics/pros-gui-template). 

## Fork Installation 
Until releases are made for this fork, the only way to install the CLI is through PIP.

For more information, please see the ``Installing for development`` section below. 

## PROS 

PROS is the only open source development environment for the VEX EDR Platform.

This project provides all of the project management related tasks for PROS. It is currently responsible for:
 - Downloading kernel templates
 - Creating, upgrading projects
 - Uploading binaries to VEX Microcontrollers

This project is built in Python 3.6, and executables are built on cx_Freeze.

## Installing for development
PROS CLI can be installed directly from source with the following prerequisites:
 - Python 3.5
 - PIP (default in Python 3.6)
 - Setuptools (default in Python 3.6)

Clone this repository, then run `pip install -e <dir>`. Pip will install all the dependencies necessary.

## About this project
Here's a quick breakdown of the packages involved in this project:

- `pros.cli`: responsible for parsing arguments and running requested command
- `pros.common.ui`: provides user interface functions used throughout the PROS CLI (such as logging facilities, machine-readable output)
- `pros.conductor`: provides all project management related tasks
    - `pros.conductor.depots`: logic for downloading templates
    - `pros.conductor.templates`: logic for maintaining information about a template
- `pros.config`: provides base classes for configuration files in PROS (and also the global cli.pros config file)
- `pros.jinx`: JINX parsing and server
- `pros.serial`: package for all serial communication with VEX Microcontrollers
- `pros.upgrade`: package for upgrading the PROS CLI, including downloading and executing installation sequence
- `pros.gui_data`: package for linking either to the ``pros-grafana`` plugin or ``WestCore-GUI``. 

See https://pros.cs.purdue.edu/v5/cli for end user documentation and developer notes.
