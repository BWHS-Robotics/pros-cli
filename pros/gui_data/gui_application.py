import struct
import threading
import time
from collections import defaultdict
from typing import *
from queue import Queue

import msgpack

import re

from pros.common import logger
from pros.serial.devices import StreamDevice
from pros.serial.terminal import Terminal

import codecs
import os
import signal
import sys
import threading

import struct

import colorama

from pros.common.utils import logger
from pros.serial import decode_bytes_to_str
from pros.serial.ports import PortConnectionException


class GUITerminal(Terminal):

    def __init__(self, port_instance: StreamDevice, transformations=(),
                 output_raw: bool = False, request_banner: bool = True):
        super().__init__(port_instance, transformations, output_raw, request_banner)

        logger(__name__).info("Attempting to connect to named pipe...")
        self.named_pipe = open(r'//./pipe/west-pros-pipe', 'wb', 0)
        logger(__name__).info("...Done!")

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

                # Instead of writing to console, write to a pipe server
                # As the C# GUI currently doesn't have support for ASCII color codes, filter them from the output See
                # https://stackoverflow.com/questions/30425105/filter-special-chars-such-as-color-codes-from-shell
                # -output for more details
                # In order to separate the data from standard cout/printf, we add a unique header prefix
                text = re.sub(r'\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))', '', text)

                encoded_message = text.encode("ascii")

                # Pack data using struct and send it to the named pipe
                self.named_pipe.write(struct.pack('I', len(encoded_message)) + encoded_message)
                self.named_pipe.seek(0)
        except UnicodeError as e:
            logger(__name__).exception(e)
        except PortConnectionException:
            logger(__name__).warning(f'Connection to {self.device.name} broken')
            if not self.alive.is_set():
                self.stop()
                self.named_pipe.close()
        except Exception as e:
            if not self.alive.is_set():
                logger(__name__).exception(e)
            else:
                logger(__name__).debug(e)
            try:
                logger(__name__).info("Beginning terminal closure..")
                self.stop()
                self.named_pipe.close()
            except Exception as exceptionException:
                logger(__name__).error("Encountered exception while closing:")
                logger(__name__).exception(exceptionException)

    def stop(self, *args):
        super().stop()

        if self.named_pipe:
            logger(__name__).info('Closing pipe...')
            self.named_pipe.close()
            logger(__name__).info('Pipe successfully closed and disposed.')
        quit()
