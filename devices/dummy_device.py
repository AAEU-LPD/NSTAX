""" Dummy device module for framework check."""


from NSTAX.devices.device import Device
from NSTAX.interface.dummy_interface import DummyInterface


class DummyDevice(Device):
    """Dummy device class."""
    def __init__(self):
        super().__init__("DummyDevice", version = 0.1)
        self.interface = None
        self.dummy_data_buffer = ""

    def connect(self):
        """Connect to the device interface."""
        self.logger.info("Establish connection for the device: %s", self.name)
        self.interface = DummyInterface()
        self.interface.connect()

    def disconnect(self):
        """Disconnect from the device interface."""
        self.logger.info("Disconnecting the device: %s", self.name)
        self.interface.disconnect()

    def send_debug_command(self, data):
        """Dummy command send"""
        self.logger.info("Sending command to the device: %s", self.name)
        self.interface.write_data(data)

    def receive_debug_readout(self):
        """Dummy device readout"""
        self.logger.info("Read from the device: %s", self.name)
        data = self.interface.read_data()
        return data
