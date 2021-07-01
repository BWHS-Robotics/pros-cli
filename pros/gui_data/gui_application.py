import os
import re
import time
import subprocess

from pros.gui_data.parser.chart_manager import ChartManager
from pros.serial.devices import StreamDevice
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

    def reader(self):

        if self.request_banner:
            try:
                self.device.write(b'pRb')
            except Exception as e:
                logger(__name__).exception(e)
        try:
            while not self.alive.is_set() and self._reader_alive:

                data = self.device.read()

                if not data:
                    continue

                text = decode_bytes_to_str(data[1])

                # As the GUI currently doesn't have support for ASCII color codes, filter them from the output See
                # https://stackoverflow.com/questions/30425105/filter-special-chars-such-as-color-codes-from-shell
                # -output for more details
                # In order to separate the data from standard cout/printf, we add a unique header prefix
                text = re.sub(r'\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))', '', text)

                # Instead of writing to console, we send the data to the ChartManager
                self.chart_manager.parse(text)
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
