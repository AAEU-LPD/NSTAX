"""Dummy system interface module for framework check."""


from time import sleep

from NSTAX.interface.interface import Interface


class DummyInterface(Interface):
    """Dummy interface class."""
    def __init__(self):
        super().__init__("DummyInterface", version = 0.1)
        self.interface_wait_time = 1

    def connect(self):
        """Connect to the Dummy interface."""
        self.logger.info("Connecting to the interface: %s", type(self).__name__)
        self.interface_handler = ""     # String to simulate data handled over connection port
        self.connected = True

    def disconnect(self):
        """Disconnect from the Dummy interface."""
        self.logger.info("Disconnecting from the interface: %s", type(self).__name__)
        self.connected = False

    def read_data(self):
        """Read payload from the Dummy port.

        :return: Data returned from the dummy device
        :rtype: str
        """
        data = self.interface_handler
        return data

    def write_data(self, data):
        """Write to the Dummy port.

        :param data: Raw data to be sent
        :type prompt: str
        """
        self.interface_handler += data
        sleep(self.interface_wait_time)
