"""Equipment driver for the IKA HS 501 Labshaker.

Purpose of this module is to control an IKA HS 501 Labshaker for arbitrary operation.
"""


from time import sleep

from NSTA.equipment.equipment import Equipment
from NSTA.interface.rs232_interface import RS232Interface


class IKAHS501(Equipment):
    """Equipment class for IKA HS 501 Labshaker.

    :param port: COM port for the shaker unit
    :type port: str
    """
    def __init__(self, port):
        super().__init__("IKAHS501", version = 0.1)
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

    def disconnect(self):
        """Disconnect the shaker"""
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


if __name__ == "__main__":
    # Example run
    Shaker = IKAHS501("COM12")   # Connect to the serial port at COM6
    Shaker.connect()            # Connect to the interface
    for i in range(5):
        Shaker.start_shaking(150)   # Start shaking at 150 RPM
        sleep(60)                   # Keep shaing for 10 seconds
        Shaker.stop()               # Stop shaking
        sleep(35*60)
    Shaker.disconnect()         # Free the COM port
