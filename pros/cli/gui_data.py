import signal
import time

import click

import pros.conductor as c
from pros.cli.common import default_options, logger, project_option, pros_root, shadow_command, resolve_v5_port
from ..gui_data.gui_application import GUITerminal
from ..serial.devices.vex import V5UserDevice
from ..serial.ports import DirectPort

@pros_root
def gui_data_cli():
    pass


@gui_data_cli.command(aliases=['gui'])
@project_option()
@click.argument('build-args', nargs=-1)
@default_options
@click.option('--banner/--no-banner', 'request_banner', default=True)
def gui_data(project: c.Project, **kwargs):
    """
    Transfers GUI data from the robot to the computer
    """
    logger(__name__).info("Starting C# GUI Application...")
    # subprocess.call(r"C:\Program Files\PROS\cli\WestCore GUI.exe") # FOR RUNNING GUI AUTOMATICALLY

    # Wait for GUI to launch
    logger(__name__).info("Application successfully started, waiting for connection")

    logger(__name__).debug(f"Finding port...")

    port = DirectPort(resolve_v5_port(None, 'user')[0])
    device = V5UserDevice(port)
    app = GUITerminal(device, request_banner=kwargs.pop('request_banner', True))

    logger(__name__).info(f"Attempting to receive data...")

    signal.signal(signal.SIGINT, app.stop)
    app.start()

    while not app.alive.is_set():
        time.sleep(0.005)
    app.join()
    logger(__name__).info("Shutting down terminal...")
