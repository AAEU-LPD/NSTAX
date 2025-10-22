"""Equipment driver for the xArm ESP32 Robotic Arm.

Purpose of this module is to control an xArm ESP32 based roboic arm as a test
equipment for specific device orientation related feature tests.
"""


from time import sleep

from NSTA.equipment.equipment import Equipment
from NSTA.interface.rs232_interface import RS232Interface


class XARM(Equipment):
    """Equipment xArm robotic hand.

    :param port: COM port for the arm
    :type port: str
    """
    def __init__(self, port):
        super().__init__("XARM", version = 0.1)
        self.port = port                # COM port for the Shaker
        self.interface = None
        self.operation_speed = 5000     # Move pperation speed (ms)
        self.waiting_time = self.operation_speed/1000 + 0.5     # Wait after start of operation (s)

    def connect(self):
        """Connect to the shaker."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        self.interface = RS232Interface(self.port, baudrate=115200, prompt=">>> ")
        # Try to connect
        try:
            self.interface.connect()
        except self.interface.CouldNotConnectError as err:
            raise self.CouldNotConnectError("Error connecting to RS232 interface via port: {}, baudrate: {}".format(self.port, 9600), orig_error_msg=str(err))
        self._init_xarm_()
        self.connected = True

    def _init_xarm_(self):
        """Initialize xArm."""
        self.restore_to_default_position()

    def disconnect(self):
        """Disconnect the arm"""
        self.restore_to_default_position()
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def set_position_raw(self, pos_vector=None):
        """Move the arm to a known position vector
        :param pos_vector: position vector for 6 servo motors
        :type pos_vector: tuple
        """
        # Check input position vector
        if len(pos_vector) != 6:
            raise self.EquipmentParameterError(f"wrong length of position vector: {len(pos_vector)}, should be 6")
        try:
            [int (i) for i in pos_vector]
        except ValueError as e_:
            raise self.EquipmentParameterError("Non integer position vector ?")
        if not 200 <= pos_vector[0] <= 700:
            raise self.EquipmentParameterError(f"Value for pos_vector(0) is out of range {pos_vector[0]}, expected: [200,700]")
        for i in range(2, 6):
            if not 35 <= pos_vector[i] <= 900:
                raise self.EquipmentParameterError(f"Value for pos_vector({i}) is out of range {pos_vector[i]}, expected: [35,900]")

        # Set to given position
        command_ = f"bus_servo.run_mult(({pos_vector[0]},{pos_vector[1]},{pos_vector[2]},{pos_vector[3]},{pos_vector[4]},{pos_vector[5]}),{self.operation_speed})"
        self.interface.write_data(command_)
        sleep(self.waiting_time)

    def restore_to_default_position(self):
        """Restore to original stable position."""
        self.set_position_raw((500,500,500,500,500,500,))


if __name__ == "__main__":
    # Example run
    Arm = XARM("COM13")   # Connect to the serial port at COM13
    Arm.connect()         # Connect to the interface
    Arm.set_position_raw((500, 500, 500, 500, 500, 500))
    Arm.disconnect()      # Free the COM port

    # Example angles
    # Arm.set_position_raw((500, 500, 500, 35, 500, 500)): 340
    # Arm.set_position_raw((500, 500, 500, 90, 500, 500)): 350
    # Arm.set_position_raw((500, 500, 500, 135, 500, 500)): 0
    # Arm.set_position_raw((500, 500, 500, 275, 500, 500)): 35
    # Arm.set_position_raw((500, 500, 500, 320, 500, 500)): 45
    # Arm.set_position_raw((500, 500, 500, 360, 500, 500)): 55
    # Arm.set_position_raw((500, 500, 500, 500, 500, 500)): 90
    # Arm.set_position_raw((500, 500, 500, 675, 500, 500)): 135
    # Arm.set_position_raw((500, 500, 500, 860, 500, 500)): 180
    # Arm.set_position_raw((500, 500, 500, 1000, 500, 500)): 212
