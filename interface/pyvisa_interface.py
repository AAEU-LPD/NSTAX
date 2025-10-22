"""Pyvisa system interface module for framework check.

Purpose of this module is to allow all SCPI programmable instruments to interface with the framework 
through their VISA driver. Handling connections, read/write and universal commands.

Install the VISA driver using:
https://www.rohde-schwarz.com/fi/applications/r-s-visa-application-note_56280-148812.html

Windows: RS_VISA_Setup_Win_7_2_5.exe
Linux (Pi): rsvisa_5.12.9_raspios_buster_arm64.deb
"""


import os
from time import sleep
import pyvisa  # Virtual Instrument Software Architecture
from NSTA.interface.interface import Interface


class PyvisaInterface(Interface):
    """Pyvisa interface class."""

    def __init__(self, serial):
        super().__init__("PyvisaInterface", version=0.1)
        self.interface_wait_time = 0.01
        try:
            if os.name == 'nt':  # Windows
                self.rm = pyvisa.ResourceManager()
            else:  # Linux
                self.rm = pyvisa.ResourceManager("/usr/lib/librsvisa.so@ivi")
        except ValueError:
            raise RuntimeWarning(
                "Install Visa driver located in README "
                "folder if you wish to use Spectrum Analyser"
                " for EoL tests!"
            )
        self.serial = serial

    def connect(self):
        """Connect to the Pyvisa interface."""
        self.logger.info("Connecting to the interface: %s",
                         type(self).__name__)
        # String to simulate data handled over connection port
        self.interface_handler = ""
        self.name = None

        for resource in self.rm.list_resources():
            if resource.startswith("USB"):
                name = resource
                device = self.rm.open_resource(name)
                check_id = device.query("*IDN?")
                if self.serial in check_id:
                    self.logger.info(f"Device Connected: {name}, {check_id}")
                    self.name = name
                    self.device = device
                else:
                    continue
            else:
                continue

        if self.name is not None:
            self.interface_handler = self.name
        else:
            raise self.CouldNotConnectError(
                "Error connecting to Pyvisa interface via port")

        self.connected = True

    def disconnect(self):
        """Disconnect from the Pyvisa interface."""
        self.device.close()
        self.logger.info(
            "Disconnecting from the interface: %s", type(self).__name__)
        self.connected = False

    def read_data(self, query):
        """Read payload from the Pyvisa port.

        :return: Data returned from the Pyvisa device
        :rtype: str
        """
        data = self.device.query(query)
        return data

    def read_data_raw(self, query):
        """Read payload from the Pyvisa port.

        :return: Data returned from the Pyvisa device
        :rtype: str
        """
        self.device.write(query)
        data = self.device.read_raw()
        return data

    def read_data_ascii(self, query):
        """Read payload from the Pyvisa port.

        :return: Data returned from the Pyvisa device
        :rtype: str
        """
        data = self.device.query_ascii_values(query)
        return data

    def write_data(self, cmd):
        """Write to the Pyvisa port.

        :param data: Raw data to be sent
        :type prompt: str
        """
        self.device.write(cmd)
        sleep(self.interface_wait_time)

    def get_device_id(self):
        """Read the device serial and other details (manufacturer details etc)

        :return: device details
        :rtype: string
        """
        id = self.read_data("*IDN?")
        return id

    def read_event_register(self):
        """Read the event registers from the instrument

        :return: register value
        :rtype: int
        """
        er = self.read_data("*ESR?")
        return er

    def enable_event_register(self):
        """Enable event register to store event values
        """
        self.write_data("*ESE")

    def clear_event_registers(self):
        """Clear event register values to zero
        """
        self.write_data("*CLS")

    def device_reset(self):
        """Reset the instrument to Factory default settings
        """
        self.write_data("*RST")
        sleep(5)

    def device_selftest(self):
        """Run a self test of the instrument
        """
        self.write_data("*TST")

    def wait_pending_operations(self):
        """Wait for pending operation to complete
        """
        self.write_data("*WAI")

    def complete_operations(self):
        """Complete all operations that are waiting or on hold
        """
        self.write_data("*OPC")


if __name__ == "__main__":
    # Example run
    VI = PyvisaInterface("SMBV100B")
    VI.connect()
    # reply = VI.read_data("*IDN?")
    # print(reply)
    reply = VI.read_data("MMEM:CDIR?")
    print(reply)
    VI.write_data('MMEM:CDIR "/var/user/Hati_Test/TEST"')
    reply = VI.read_data("MMEM:CDIR?")
    print(reply)
    # VI.write_data('SOUR:BB:GNSS:SETT:LOAD "brazil"')
    # VI.write_data('SOUR:BB:GNSS:SETT:LOAD "munich"')
    # VI.write_data('SOUR:BB:GNSS:SETT:LOAD "london"')
    # VI.write_data('SOUR:BB:GNSS:SETT:LOAD "ocean"')
    # VI.write_data('SOUR:BB:GNSS:SETT:LOAD "america"')
    VI.disconnect()