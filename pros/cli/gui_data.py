import os
import subprocess
import signal
import time
from typing import *

import click

import pros.conductor as c
from pros.cli.common import default_options, logger, project_option, pros_root, shadow_command, resolve_v5_port
from .upload import upload
from ..gui_data.gui_application import GUITerminal
from ..serial.devices.vex import V5UserDevice
from ..serial.ports import DirectPort


@pros_root
def gui_data_cli():
    pass


@gui_data_cli.command(aliases=['build'])
@project_option()
@click.argument('build-args', nargs=-1)
@default_options
def gui_data(project: c.Project, build_args):
    """
    Transfers GUI data from the robot to the computer
    """

    logger(__name__).info("Starting C# GUI Application...")
    # subprocess.call(r"C:\Program Files\PROS\cli\WestCore GUI.exe") # FOR RUNNING GUI AUTOMATICALLY

    # Wait for GUI to launch
    time.sleep(5)  # TODO: Don't have a manual sleep here
    logger(__name__).info("Application successfully started, waiting for connection")

    logger(__name__).debug(f"Finding port...")

    port = DirectPort(resolve_v5_port(None, 'user')[0])
    device = V5UserDevice(port)
    app = GUITerminal(device)

    logger(__name__).info(f"Attempting to receive data...")

    signal.signal(signal.SIGINT, app.stop)
    app.start()

    while not app.alive.is_set():
        time.sleep(0.005)
    app.join()
    logger(__name__).info("Shutting down terminal...")
