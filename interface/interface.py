"""Base Module for System Interfaces.

This module contains the base class for system interfaces. Any new interface
module needs to be inherited from this.

Contents of this modules are not for instantiation.
"""


import logging


class Interface:
    """Base Interface Class to be inherited for new interface development.

    :param name: Unique interface name
    :type name: str
    :param version: Module version, defaults to 0.0
    :type version: float, optional
    """
    def __init__(self, name, version = 0.0):
        """Constructor."""
        self.name = name
        self.version = version
        self.connected = False              # Connection status indicator
        self.interface_handler = None
        self.logger = logging.getLogger('NSTA.{}'.format(__name__))   # Logger instance
        self.CouldNotConnectError = type("CouldNotConnectError", (InterfaceExcption,), {"name": self.name})

    def connect(self):
        """Connect to the interface."""

    def disconnect(self):
        """Free the connection port."""

    def read_data(self):
        """Read from the connected interface."""

    def write_data(self, data):
        """Write to the connected interface."""

    def is_connected(self):
        """Check if still connected to the if.

        :return: `True` if connected, `False` otherwise
        :rtype: bool
        """
        return self.connected


class InterfaceExcption(Exception):
    """ABC for all exceptions relevant for device interfaces."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.orig_error_msg = kwargs.get("orig_error_msg")
