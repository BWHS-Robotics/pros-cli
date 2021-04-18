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

    logger(__name__).debug(f"Finding port...")

    port = DirectPort(resolve_v5_port(None, 'user')[0])
    device = V5UserDevice(port)
    app = GUITerminal(device)

    logger(__name__).info(f"Attempting to receive data...")
    app.start()

    while True:
        time.sleep(1)