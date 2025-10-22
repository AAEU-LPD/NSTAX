"""Equipment driver for the IKA KS 130 Labshaker.

Purpose of this module is to control an IKA KS 130 Labshaker for arbitrary operation.
"""


from time import sleep

from NSTAX.equipment.equipment import Equipment
from NSTAX.interface.rs232_interface import RS232Interface

# Error Codes
error_codes = {
    -1: "GEN_ERR",
    -2: "NO_COMM",
    -3: "HIGH_TEMP",
    -4: "MOTOR_OVERLOAD",
    -9: "VALUE_ERR",
    -41: "TRIAC_DEV_ERR",
    -42: "SAFETY_DEV_ERR",
    -83: "WRONG_PARITY",
    -84: "UNKOWN_INSTR",
    -85: "WRONG_INSTR_SEQ",
    -86: "INV_RATED_VAL",
    -87: "INSUFF_STORAGE"
}


class IKAKS130(Equipment):
    """Equipment class for IKA KS 130 Labshaker.

    :param port: COM port for the shaker unit
    :type port: str
    """

    def __init__(self, port):
        super().__init__("IKAKS130", version=0.1)
        self.port = port        # COM port for the Shaker
        self.interface = None

    def connect(self):
        """Connect to the shaker."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        self.interface = RS232Interface(self.port, baudrate=9600, EOL="\r\n", bytesize=7, stopbits=1, parity="E", rtscts=True)
        # Try to connect
        try:
            self.interface.connect()
        except self.interface.CouldNotConnectError as err:
            raise self.CouldNotConnectError("Error connecting to RS232 interface via port: {}, baudrate: {}".format(self.port, 9600), orig_error_msg=str(err))
        self._init_shaker_()
        self.connected = True

    def _init_shaker_(self):
        """Enable remote function."""
        self.interface.write_data("START_4")

    def _deinit_shaker_(self):
        """Enable remote function."""
        self.interface.write_data("STOP_4")

    def disconnect(self):
        """Disconnect the shaker"""
        self._deinit_shaker_()
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def start_shaking(self, rpm):
        """Start shaking over a given RPM"""
        cmd = "OUT_SP_4 {}".format(rpm)
        self.interface.write_data(cmd)

    def stop(self):
        """Stop shaking"""
        cmd = "OUT_SP_4 0"
        self.interface.write_data(cmd)

    def read_real_value(self):
        """Read real value from device"""
        data = self.interface.communicate_data("IN_PV_4")
        return data

    def read_set_value(self):
        """Read real value from device"""
        data = self.interface.communicate_data("IN_SP_4")
        return data

    def read_set_range(self):
        """Read real value from device"""
        data = self.interface.communicate_data(f"IN_SP_6")
        return data

    def read_dev_status(self):
        """Read/Display device status"""
        data = self.interface.communicate_data("STATUS")
        return data
        # TODO: check error data type
        # if int(data) < 0:
        #     # Check if the data is in the error_codes dictionary
        #     error_message = error_codes.get(data, "UNKNOWN_ERROR_CODE")
        #     print(error_message)

    def read_dev_type(self):
        """Read/Display device type"""
        data = self.interface.communicate_data("IN_TYPE")
        return data

    def read_dev_name(self):
        """Read/Display device name"""
        data = self.interface.communicate_data("IN_NAME")
        return data

    def write_dev_name(self, name):
        """Write device name"""
        if len(name) > 6:
            name[6:]
        self.interface.write_data(f"OUT_NAME {name}")

    def reset_device(self):
        """Reset the device"""
        self.interface.write_data("RESET")


if __name__ == "__main__":
    shake_min = 2*60
    shake_rpm = 600
    # Example run
    Shaker = IKAKS130("/dev/ttyUSB0")   # Connect to the serial port at COM6
    Shaker.connect()            # Connect to the interface
    Shaker.start_shaking(shake_rpm)   # Start shaking at 150 RPM
    # Shaker.read_dev_type()
    # Shaker.read_dev_name()
    # Shaker.read_dev_status()
    # Shaker.read_real_value()
    # Shaker.read_set_value()
    # Shaker.read_set_range()
    sleep(shake_min*60)                   # Keep shaing for 10 seconds
    # Shaker.reset_device()
    Shaker.stop()               # Stop shaking
    Shaker.disconnect()         # Free the COM port
