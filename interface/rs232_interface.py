"""Interface module to the RS232 serial interface.

Purpose of this module is to control DUTs and equipment supporting RS232 serial as
connection medium.
"""


import queue
from time import sleep
import re
import string
import serial
import threading
import csv
import time
from datetime import datetime
import logging

from NSTAX.interface.interface import Interface


class RS232Interface(Interface):
    """RS232 interface class.

    :param port: COM port name of the target interface
    :type port: str
    :param baudrate: COM port baud rate, default: 115200
    :type baudrate: int, optional
    :param prompt: Console prefix specific to unit under connection, default: <blank>
    :type prompt: str, optional
    :param EOL: End of line character for the console, default: \r
    :type EOL: str, optional
    :param bin_cmd: Use raw data for I/O if enabled, further formatting (prompt, EOL) are disabled, default: False
    :type bin_cmd: bool, optional
    :param interface_wait_time: Waiting time between interface calls, default: 0.1s
    :type interface_wait_time: float, optional
    """
    def __init__(self, port, baudrate=115200, prompt="", EOL="\r", bin_cmd=False, interface_wait_time=0.1, bytesize=8, stopbits=1.0, parity="N", rtscts=False, timeout=None):
        super().__init__("RS232", version = 0.1)
        # General Serial Interface parameters
        self.interface_wait_time = interface_wait_time
        self.interface_handler = None
        self.port = port
        self.baudrate = baudrate
        self.bytesize = bytesize
        self.stopbits = stopbits
        self.parity = parity
        self.rtscts = rtscts
        self.timeout = timeout
        self.prompt = prompt
        self.EOL = EOL
        self.bin_cmd = bin_cmd
        self.tx_data = ""
        if self.bin_cmd:
            # Convert all strings to bins
            self.prompt, self.EOL, self.tx_data =  self._str_to_bin((self.prompt, self.EOL, self.tx_data,))
        # For thread based operations
        self.in_measurement = False
        self.serial_thread = None
        self.lock = threading.Lock()
        self.data_queue = queue.Queue()

    def _str_to_bin(self, arg_list=None):
        ret_arg_list = []
        for arg_ in arg_list:
            if isinstance(arg_, str):
                ret_arg_list.append(arg_.encode("utf-8"))
            else:
                ret_arg_list.append(arg_)
        return ret_arg_list

    def connect(self):
        """Connect to the RS232 interface."""
        self.logger.info("Connecting to the interface: %s", type(self).__name__)
        try:
            self.interface_handler = serial.Serial(timeout=self.timeout, port=self.port, baudrate=self.baudrate, bytesize=self.bytesize, parity=self.parity, rtscts=self.rtscts)
        except serial.SerialException as err:
            raise self.CouldNotConnectError("Error connecting to RS232 interface via port: {}, baudrate: {}".format(self.port, self.baudrate), orig_error_msg=str(err))
        self.connected = True

    def disconnect(self):
        """Disconnect from the RS232 interface."""
        self.logger.info("Disconnecting from the interface: %s", type(self).__name__)
        self.read_data_stream_stop()  # Ensure thread is stopped
        if self.interface_handler:
            self.interface_handler.close()
            self.interface_handler = None
        self.connected = False

    def read_data(self, prompt=None, strip_tx=True):
        """Read payload from the RS232 port.

        Payload is the content between last encounter and the prompt.

        :param prompt: Console prefix specific to unit under connection, default: <blank>
        :type prompt: str, optional
        :param strip_tx: Strip the sent (if any) sent bytes during previous steps, default: False
        :type prompt: str, optional

        :return: Data returned from the device over serial port
        :rtype: str
        """
        if prompt == None:
            prompt = self.prompt
        blank_char = ""
        if self.bin_cmd:
            if isinstance(prompt, str):
                prompt = self._str_to_bin((prompt,))
            blank_char = b""
        rx_data = blank_char
        errors = 0
        while True:
            sleep(self.interface_wait_time)
            bytes_ = self.interface_handler.in_waiting
            if not bytes_:
                errors += 1
                if errors > 9:
                    break       # Prevent inf loop
                continue
            data_part = self.interface_handler.read(bytes_)
            if not self.bin_cmd:
                data_part = data_part.decode("utf-8")
            if data_part:
                rx_data += data_part
                if re.search(self.prompt, rx_data):
                    break
        if self.bin_cmd:
            data = rx_data
        else:
            printable = lambda str_: blank_char.join(s_ for s_ in str_ if s_ in string.printable)
            data = printable(rx_data)   # Filter only printable characters
        # TODO: Strip sent/command data
        if strip_tx:
            data = data.replace(self.tx_data, blank_char)
        data = re.sub(self.prompt, blank_char, data)                # Strip prompt data
        data = data.replace(self.prompt, blank_char)
        if not self.bin_cmd:
            # remove outer spaces for human readable strings
            data = data.strip()
        return data

    def write_data(self, data):
        """Write to the RS232 port.

        :param data: Serial command
        :type prompt: str
        """
        if self.bin_cmd:
            serial_cmd = data
            self.tx_data = serial_cmd
        else:
            serial_cmd = "{}{}".format(data, self.EOL)
            self.tx_data = serial_cmd
            serial_cmd = serial_cmd.encode()
        self.logger.info("Writing to the %s interface: %s", type(self).__name__, serial_cmd)
        self.interface_handler.write(serial_cmd)
        sleep(self.interface_wait_time)

    def communicate_data(self, data, prompt=None, strip_tx=True):
        """Write / read combined.

        This method is targeted to equipment where every write commands return
        meaningful return messages.

        Separated read_data() and write_data() can anyway be used instead of
        this method, but then the driver code must take care of clearing the
        read buffer in cases where multiple messages are to be sent in order to
        obtain a single return / read value.

        :param data: Serial command
        :type prompt: str
        :param prompt: Console prefix specific to unit under connection, default: <blank>
        :type prompt: str, optional
        :param strip_tx: Strip the sent (if any) sent bytes during previous steps, default: False
        :type prompt: str, optional

        :return: Data returned from the device over serial port
        :rtype: str
        """
        self.write_data(data)
        ret_data = self.read_data(prompt=prompt, strip_tx=strip_tx)
        return ret_data
    
    def read_data_stream_start(self, timestamp_en=True):
        """Start a new thread for logging.

        :param timestamp_en: Enable or disable timestamps in logged data
        :type timestamp_en: bool, optional
        """
        with self.lock:
            if self.serial_thread and self.serial_thread.is_alive():
                self.logger.warning("Serial thread already running.")
                return
            self.in_measurement = True
        # Create and start a thread for logging serial data
        self.serial_thread = threading.Thread(
            target=self._read_data_stream_thread,
            kwargs={"timestamp_en": timestamp_en},
            daemon=True
        )
        self.serial_thread.start()

    def read_data_stream_stop(self):
        """Await running logger thread and end measurement"""
        with self.lock:
            self.in_measurement = False
        if self.serial_thread:
            # Wait for the serial thread to complete
            self.serial_thread.join(timeout=5.0)
            self.serial_thread = None
        if not self.data_queue.empty():
            return self.data_queue.get()
        return None
    
    def save_data_stream_to_csv(self, file_path, data_stream):
        """
        Save the provided data stream payload to a CSV file.

        :param file_path: Path to the CSV file
        :type file_path: str
        :param data_stream: Data stream payload to save
        :type data_stream: str or bytes
        """
        if not data_stream:
            self.logger.warning("No data stream payload provided. Nothing to save.")
            return

        with open(file_path, mode='w', encoding='utf-8') as file:
            if isinstance(data_stream, bytes):
                data_stream = data_stream.decode("utf-8", errors="replace")
            for line in data_stream.split('\n'):
                file.write(f"{line}\n")
        self.logger.info(f"Data stream saved to file: {file_path}")
        
    def _read_data_stream_thread(self, timestamp_en=True):
        """
        Continuously read data from the RS232 port until in_measurement is False.
        Each line is optionally prepended with a timestamp.

        :param timestamp_en: If True, prepend each line with a timestamp
        :type timestamp_en: bool, optional
        :return: Data chunk read from the device over serial port
        :rtype: str or bytes
        """
        blank_char = b"" if self.bin_cmd else ""
        data = []
        errors = 0
        while self.in_measurement:
            if self.interface_handler.in_waiting:
                try:
                    line = self.interface_handler.readline()
                except serial.SerialException as e:
                    err_str = "PORT_ERROR"
                    self.logger.error(f"Exception in data stream thread: {e} err_str: {err_str}")
                    break
                self.logger.debug(f"|LOGGER_DEBUG|:{line}")
                if timestamp_en:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                if not self.bin_cmd:
                    line = line.decode("utf-8").strip()
                    if timestamp_en:
                        line_with_ts = f"[{timestamp}] {line}\n"
                    else:
                        line_with_ts = f"{line}\n"
                else:
                    if timestamp_en:
                        line_with_ts = timestamp.encode("utf-8") + b" " + line.rstrip(b"\r\n") + b"\n"
                    else:
                        line_with_ts = line.rstrip(b"\r\n") + b"\n"
                data.append(line_with_ts)
                errors = 0
                sleep(self.interface_wait_time)
            else:
                errors += 1
                if errors > 9:
                    self.logger.warning("No data received for 10 cycles, stopping thread.")
                    break
                sleep(self.interface_wait_time)
        self.logger.info("Serial data stream thread exiting.")
        if self.bin_cmd:
            self.data_queue.put(b"".join(data))
        else:
            data = "".join(data)
            printable = lambda s: blank_char.join(c for c in s if c in string.printable)
            self.data_queue.put(printable(data).strip())
            

if __name__ == "__main__":
    # Example run on IKA Labshaker
    SI = RS232Interface("COM10",interface_wait_time=10, timeout=600, baudrate=115200)
    SI.connect()
    # sleep(60)
    # data = SI.read_data()
    SI.read_data_stream_start()
    sleep(30)
    result = SI.read_data_stream_stop()
    print(result)
    SI.save_data_stream_to_csv("test_serial_data.csv", result)
    SI.disconnect()

    """
    # Example run on uPython
    SI = RS232Interface("COM5", baudrate=115200, prompt=">>> ")
    SI.connect()

    SI.write_data("print('Hi...')")
    SI.write_data("bus_servo.run_mult((500,700,500,500,500,500),1500)")
    SI.write_data("bus_servo.run_mult((500,500,500,500,500,500),1500)")

    print(SI.read_data())
    SI.disconnect()
    """

    """
    # Example run with binary commands
    SI = RS232Interface("COM3", baudrate=19200, bin_cmd=True)
    SI.connect()
    SI.write_data(b'\x06\x00\x02\x04')
    sleep(1)
    data_ = SI.read_data()
    sleep(2)
    SI.write_data(b'\x07\x00\x02\x05')

    SI.disconnect()
    """
