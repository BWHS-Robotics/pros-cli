import os
import re
import threading
import time
import subprocess

from pros.serial.devices import StreamDevice
from pros.serial.ports.v5_wireless_port import V5WirelessPort
from pros.serial.terminal import Terminal

import struct

from pros.common.utils import logger
from pros.serial import decode_bytes_to_str
from pros.serial.ports import PortConnectionException


class GUITerminal(Terminal):
    GUI_EXE_PATH = r"C:\Program Files (x86)\GUI_WPF_Migration-Installer\GUI-WPF-Migration.exe"

    def __init__(self, port_instance: StreamDevice, transformations=(),
                 output_raw: bool = False, request_banner: bool = True):
        super().__init__(port_instance, transformations, output_raw, request_banner)

        self.wireless = port_instance.port is V5WirelessPort

        print(type(port_instance.port))

        try:
            # Launch C# GUI EXE
            # TODO: The path is currently hardcoded. Find a way to autodetect where it is?
            logger(__name__).info("Launching exe...")
            subprocess.Popen(self.GUI_EXE_PATH)

            while True:
                try:
                    if not self.wireless:
                        logger(__name__).info("Attempting to connect to the reader named pipe...")

                        # Names are from the perspective of the CLI
                        self.reader_named_pipe = open(r'//./pipe/pros-gui-reader-pipe', 'r', buffering=1)

                        logger(__name__).info("...Done!")

                    logger(__name__).info("Attempting to connect to the writer named pipe...")

                    # Names are from the perspective of the CLI
                    self.writer_named_pipe = open(r'//./pipe/pros-gui-writer-pipe', 'wb+', 0)
                    logger(__name__).info("...Done!")
                    break
                except (OSError, BrokenPipeError):
                    time.sleep(0.5)

        except FileNotFoundError as e:
            logger(__name__).error("The GUI executable path was not found. Are you sure you installed it?",
                                   extra={'sentry': False})
            exit()  # Probably shouldn't use exit here, oh well!

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

                # Instead of writing to console, write to a pipe server
                # As the C# GUI currently doesn't have support for ASCII color codes, filter them from the output See
                # https://stackoverflow.com/questions/30425105/filter-special-chars-such-as-color-codes-from-shell
                # -output for more details
                # In order to separate the data from standard cout/printf, we add a unique header prefix
                text = re.sub(r'\x1b(\[.*?[@-~]|\].*?(\x07|\x1b\\))', '', text)

                encoded_message = text.encode("ascii")

                # Pack data using struct and send it to the named pipe
                self.writer_named_pipe.write(struct.pack('I', len(encoded_message)) + encoded_message)
                self.writer_named_pipe.seek(0)
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
            self._begin_terminal_closure(e)

    def _start_gui_rx(self):
        self._gui_reader_alive = True
        self.gui_reader_thread = threading.Thread(target=self.gui_reader,
                                                  name='gui-reader')
        self.gui_reader_thread.daemon = True
        self.gui_reader_thread.start()

    def _stop_gui_rx(self):
        self._gui_reader_alive = False
        self.gui_reader_thread.join()

    def start(self, *args):
        super().start()

        if not self.wireless:
            self._start_gui_rx()

    def stop(self, *args):
        super().stop()

        self._stop_gui_rx()

        # Dispose of named pipe connections
        logger(__name__).info('Closing pipes...')
        if self.writer_named_pipe:
            self.writer_named_pipe.close()
        if self.reader_named_pipe:
            self.reader_named_pipe.close()
        logger(__name__).info('Pipes successfully closed and disposed.')
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
