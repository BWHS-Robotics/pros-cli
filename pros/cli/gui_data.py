import os
import signal
import time

import click

import pros.conductor as c
from pros.cli.common import default_options, logger, project_option, pros_root, shadow_command, resolve_v5_port, \
    resolve_cortex_port
from ..gui_data.gui_application import GUITerminal
from ..serial.ports import DirectPort
import pros.serial.devices as devices
from ..serial.ports.v5_wireless_port import V5WirelessPort


@pros_root
def gui_data_cli():
    pass


@gui_data_cli.command(aliases=['gui', 'g'])
@default_options
@click.argument('port', default='default')
@click.option('--backend', type=click.Choice(['share', 'solo']), default='solo',
              help='Backend port of the terminal. See above for details')
@click.option('--banner/--no-banner', 'request_banner', default=True)
def gui_data(port: str, backend: str, **kwargs):
    """
    Transfers GUI data from the robot to the computer
    """
    from pros.serial.devices.vex.v5_user_device import V5UserDevice
    from pros.serial.terminal import Terminal
    is_v5_user_joystick = False
    if port == 'default':
        project_path = c.Project.find_project(os.getcwd())
        if project_path is None:
            v5_port, is_v5_user_joystick = resolve_v5_port(None, 'user', quiet=True)
            cortex_port = resolve_cortex_port(None, quiet=True)
            if ((v5_port is None) ^ (cortex_port is None)) or (v5_port is not None and v5_port == cortex_port):
                port = v5_port or cortex_port
            else:
                raise click.UsageError('You must be in a PROS project directory to enable default port selecting')
        else:
            project = c.Project(project_path)
            port = project.target

    if port == 'v5':
        port = None
        port, is_v5_user_joystick = resolve_v5_port(port, 'user')
    elif port == 'cortex':
        port = None
        port = resolve_cortex_port(port)
        kwargs['raw'] = True
    if not port:
        return -1

    if backend == 'share':
        raise NotImplementedError('Share backend is not yet implemented')
        # ser = SerialSharePort(port)
    elif is_v5_user_joystick:
        logger(__name__).debug("it's a v5 joystick")
        ser = V5WirelessPort(port)
    else:
        logger(__name__).debug("not a v5 joystick")
        ser = DirectPort(port)
    if kwargs.get('raw', False):
        device = devices.RawStreamDevice(ser)
    else:
        device = devices.vex.V5UserDevice(ser)

    app = GUITerminal(device, request_banner=kwargs.pop('request_banner', True))

    logger(__name__).info(f"Attempting to receive data...")

    signal.signal(signal.SIGINT, app.stop)
    app.start()

    while not app.alive.is_set():
        time.sleep(0.005)
    app.join()
    logger(__name__).info("Shutting down terminal...")
