""" Generic module for a Logging instance on suported serial devices.

Purpose of this module is to connect any device (SF/NBIoT/...) or Equipment that is
connected through a cable to loggable device using its COM port
"""

import threading
import serial
import time
from datetime import datetime
import logging

class Logger:
    """Generic logger for serial devices.

    :param name: Unique name label of device
    :type name: str
    :param port: COM port connected for logging, defaults to ""
    :type port: str, optional
    :param log_timestamps: timestamps append to logged data, defaults to True
    :type log_timestamps: bool, optional
    :param auto_start: automatically start logging on connect, defaults to True
    :type auto_start: bool, optional
    :param file_path: folder to store recorded logs, defaults to "."
    :type file_path: str, optional
    """

    def __init__(self, name, port="", log_timestamps=True, auto_start=True, file_path="."):
        self.name = name
        self.port = port
        self.data_filename = f'{file_path}\\{name}_serial_data.csv'
        self.log_timestamps = log_timestamps
        self.auto_start = auto_start
        self.log_folder = file_path
        self.in_measurement = False
        self.serial_thread = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(f'NSTA.{__name__}')
        self.is_connected = False
        self._check_port()
        
    def connect(self, log_folder):
        """Connect to a logging instance and start logging if auto_start is True."""
        self._set_logfile_path(log_folder)
        if self.auto_start:
            self.start_logger()
            self.is_connected = True

    def disconnect(self):
        """Disconnect from the logging instance."""
        if self.is_connected:
            self.is_connected = False
            self.stop_logger()

    def _check_port(self):
        """Check if the specified port is available for connection"""
        try:
            ser = serial.Serial(self.port, 115200, timeout=1, rtscts=True)
            ser.close()
        except serial.SerialException:
            raise RuntimeError(f"COM port '{self.port}' not found. Check parameters")

    def _connect_serial(self):
        """Connect to the serial COM port and log data."""
        ser = serial.Serial(self.port, 115200, timeout=1)
        err_str = "LOG_COMPLETE"
        with open(self.data_filename, mode='w', newline='') as file:
            while self.in_measurement:
                try:
                    data = ser.readline().decode().strip()
                except serial.SerialException:
                    err_str = "PORT_ERROR"
                    break
                if data:
                    if self.log_timestamps:
                        timestamp_utc = datetime.utcnow().strftime('[%Y-%m-%d %H:%M:%S.%f]')
                        row_to_write = f"{timestamp_utc} {data}\n"
                    else:
                        row_to_write = f"{data}\n"
                    file.write(row_to_write)
        self.logger.info(f"Closing COM port: {self.port} ,Status: {err_str}")
        if err_str != "LOG_COMPLETE":
            return -1
        ser.close()
        return 0

    def _set_logfile_path(self, path):
        """Set a custom path to save the generated log."""
        self.log_folder = path
        self.data_filename = f'{path}\\{self.name}_serial_data.csv'

    def get_device_port(self):
        """Get the COM port of the connected device."""
        return self.port

    def get_log_folder(self):
        """Get the folder where logs are stored."""
        return self.log_folder

    def start_logger(self):
        """Start a new thread for logging."""
        with self.lock:
            self.in_measurement = True
        self.serial_thread = threading.Thread(target=self._connect_serial)
        self.serial_thread.start()

    def stop_logger(self):
        """Await running logger thread and end measurement."""
        with self.lock:
            self.in_measurement = False
        if self.serial_thread:
            self.serial_thread.join(timeout=5.0)
            self.serial_thread = None
            
    # TEST FUNCTIONS
    def connect_manual(self):
        """Manually connect to the logging instance (TEST: Don't Use!)"""
        self.start_logger()

    def disconnect_manual(self):
        """Manually disconnect from the logging instance (TEST: Don't Use!)"""
        self.stop_logger()
    # END TEST FUNCTIONS

if __name__ == '__main__':
    logger = Logger('HATI', 'COM6')
    print('---Logging started\n')
    logger.start_logger()
    time.sleep(20)
    logger.stop_logger()
    print('---Logging finished successfully\n')
