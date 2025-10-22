"""Base module for equipments.

This module contains the base class for equipment. Any new test equipment need
to be inherited from this.

Contents of this modules are not for instantiation.
"""


import logging


class Equipment:
    """Base class to be inherited for new equipment implementation.

    :param name: Unique equipment name
    :type name: str
    :param version: Module version, default: 0.0
    :type version: str, optional
    """
    def __init__(self, name, version = 0.0):
        self.name = name
        self.version = version
        self.connected = False      # Connection status indicator
        self.connection_instance = None
        self.logger = logging.getLogger('NSTA.{}'.format(__name__))

        self.CouldNotConnectError = type("CouldNotConnectError", (EquipmentExcption,), {"name": self.name})
        self.EquipmentParameterError = type("WrongEquipmentParameterError", (EquipmentExcption,), {"name": self.name})

    def connect(self):
        """Connect to the equipment."""

    def disconnect(self):
        """Free the connection port."""

    def read_data(self):
        """Read from the connected equipment."""

    def write_data(self):
        """Write to the connected equipment."""

    def is_connected(self):
        """Check if still connected.
        
        Returns:
            bool: True for being connected, False otherwise.
        """
        return self.connected


class EquipmentExcption(Exception):
    """ABC for all exceptions relevant for equipment."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.orig_error_msg = kwargs.get("orig_error_msg")
