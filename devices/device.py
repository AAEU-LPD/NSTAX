""" Base module for Devices.

This module contains the base class for devices. Any new devices need to be
inherited from this.

Contents of this modules are not for instantiation.
"""


import logging


class Device:
    """Base Device Class to be inherited for new device development.

    :param type: Unique device type
    :type type: str
    :param version: Module version, default: 0.0
    :type version: str, optional
    """
    def __init__(self, type, version = 0.0):
        self.type = type
        self.version = version
        self.info = ""
        self.interface = None
        self.logger = logging.getLogger('NSTA.{}'.format(__name__))

    def connect(self):
        """Connect to the device."""

    def disconnect(self):
        """Disconnect from the device."""

    def is_connected(self):
        """Checks device connectivity.

        Returns:
            bool: True for being connected, False otherwise.
        """
        return self.interface.connected
