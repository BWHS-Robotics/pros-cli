import os
import re
import threading
import time
import subprocess

from pros.gui_data.parser.chart_manager import ChartManager
from pros.serial.devices import StreamDevice
from pros.serial.ports.v5_wireless_port import V5WirelessPort
from pros.serial.terminal import Terminal

import struct

from pros.common.utils import logger
from pros.serial import decode_bytes_to_str
from pros.serial.ports import PortConnectionException


class GUITerminal(Terminal):
    def __init__(self, port_instance: StreamDevice, transformations=(),
                 output_raw: bool = False, request_banner: bool = True):
        super().__init__(port_instance, transformations, output_raw, request_banner)

        self.chart_manager = ChartManager()

        self.gui_reader_thread = None  # type: threading.Thread
        self._gui_reader_alive = None

    def gui_reader(self):
        # Until wireless input is supported, just return for now
        if self.wireless:
            return
        try:
            while not self.alive.is_set() and self._gui_reader_alive:
                if self.reader_named_pipe:
                    data = self.reader_named_pipe.readline().strip() + "\n"

                    if len(data) == 0:
                        print("GUI Connection Lost, Closing...")
                        break

                    # Send the data to the STDIN of the PROS program
                    self.device.write(data.encode(encoding='utf-8'))
        except UnicodeError as e:
            logger(__name__).exception(e)
        except PortConnectionException:
            if not self.alive.is_set():
                logger(__name__).warning(f'Connection to {self.device.name} broken')
                self.stop()
        except (BrokenPipeError, OSError):
            if not self.alive.is_set():
                logger(__name__).warning('Connection to GUI was abruptly stopped. Closing terminal...')
                self.stop()
        except Exception as e:
            self._begin_terminal_closure(e)

    def reader(self):

        self.device.write(b'pRb')

        try:
            while not self.alive.is_set() and self._reader_alive:

                data = self.device.read()

                if not data:
                    continue

                text = decode_bytes_to_str(data[1])

                # Instead of writing to console, we send the data to the ChartManager
                self.chart_manager.parse(self, text)

        except UnicodeError as e:
            logger(__name__).exception(e)
        except PortConnectionException:
            logger(__name__).warning(f'Connection to {self.device.name} broken')
            if not self.alive.is_set():
                self.stop()
        except (BrokenPipeError, OSError) as e:
            logger(__name__).warning('Connection to GUI was abruptly stopped. Closing terminal...')
            if not self.alive.is_set():
                self.stop()
        except Exception as e:
            if not self.alive.is_set():
                logger(__name__).exception(e)
            else:
                logger(__name__).debug(e)
            try:
                logger(__name__).info("Beginning terminal closure..")
                self.stop()
            except Exception as exceptionException:
                logger(__name__).error("Encountered exception while closing:")
                logger(__name__).exception(exceptionException)

    def stop(self, *args):
        super().stop()
        quit()

    def _begin_terminal_closure(self, e):
        if not self.alive.is_set():
            logger(__name__).exception(e)
        else:
            logger(__name__).debug(e)
        try:
            logger(__name__).info("Beginning terminal closure..")
            self.stop()
        except Exception as exceptionException:
            logger(__name__).error("Encountered exception while closing:")
            logger(__name__).exception(exceptionException)
