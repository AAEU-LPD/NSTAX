""" Generic module for Serial Logging suported devices.

Purpose of this module is to represent any device with UART connection is
connected and accessable through a COM port
"""
from time import sleep

from NSTAX.devices.device import Device
from NSTAX.interface.rs232_interface import RS232Interface

class SerialDevice(Device):
    """Generic platform connected device base class.

    :param name: Unique name label of device
    :type name: str
    :param device_id: Sensolus Device ID, defaults to ""
    :type device_id: str, optional
    """
    def __init__(self, name, port, device_id="", serial_timeout_s=10, baudrate=115200, timeout=600):
        super().__init__("SerialDevice", version = 0.1)
        self.device_id = device_id
        self.name = name
        self.port = port
        self.timeout = timeout
        self.baudrate = baudrate
        self.serial_timeout_s = serial_timeout_s
        self.interface = None
        self.data = None

    def connect(self):
        """Connect to the device interface."""
        self.logger.info("Establish connection for the device: %s", self.name)
        self.interface = RS232Interface(port=self.port, interface_wait_time=self.serial_timeout_s, timeout=self.timeout, baudrate=self.baudrate)
        self.interface.connect()

    def disconnect(self):
        """Disconnect from the device interface."""
        self.logger.info("Disconnecting the device: %s", self.name)
        self.interface.disconnect()

    def read_serial_data_start(self, timestamp_en=False):
        """Start reading data from the serial interface."""
        self.logger.info("Started reading data from the device: %s", self.name)
        self.interface.read_data_stream_start(timestamp_en=timestamp_en)

    def read_serial_data_stop(self):
        """Stop reading data from the serial interface."""
        self.data = self.interface.read_data_stream_stop()
        self.logger.info("Stopped reading data from the device: %s", self.name)

    def get_serial_data(self):
        """Get the data read from the serial interface."""
        if not hasattr(self, "data") or self.data is None:
            self.logger.warning("No serial data available for device: %s", self.name)
            return None
        return self.data

    def save_serial_data(self, filename="serial_data.csv"):
        """Save the data read from the serial interface to a CSV file."""
        if self.data is not None:
            self.interface.save_data_stream_to_csv(filename, self.data)
        else:
            self.logger.warning("No data available to save for device: %s", self.name)
            
if __name__ == "__main__":
    # Sample usage of SerialDevice
    device = SerialDevice(name="SerialDevice", port="COM10", device_id="12345", serial_timeout_s=10)
    device.connect()
    device.read_serial_data_start(timestamp_en=True)
    sleep(30)  # Simulate reading for 30 seconds
    device.read_serial_data_stop()
    data = device.get_serial_data()
    print("Serial Data:", data)
    device.save_serial_data("output_serial_data.csv")
    device.disconnect()
