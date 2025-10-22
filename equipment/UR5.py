"""Equipment driver for the Universal Robot Robots UR5 Robotic Arm.

Purpose of this module is to control the UR5 as a test equipment for specific device orientation related feature tests.
"""


from time import sleep
from math import pi
import socket

from NSTA.equipment.equipment import Equipment


class UR5(Equipment):
    """Equipment UR5 robotic arm.

    :param ip_address: IP address
    :type port: str
    :param port: Connection port, defaults to 30002
    :type port: int, optional
    """
    def __init__(self, ip_address, port=30002):
        super().__init__("UR5", version = 0.1)
        self.ip_address = ip_address
        self.port = port
        self.interface = None
        self.joint_speed = 0.5          # joint speed of leading axis [rad/s]
        self.joint_acceleration = 1.0   # joint acceleration of leading axis [rad/s^2]
        self.newline_char = "\n"
        self.operation_settling_time = 5    # Movement operation timeout (s)

    def connect(self):
        """Connect to the arm."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        try:
            self.interface = socket.create_connection((self.ip_address, self.port,), timeout=5)
            self.connected = True
        except socket.error as e_:
            raise self.CouldNotConnectError(f"Error connecting to the interface via IP: {self.ip_address}, port: {self.port}", orig_error_msg=set(e_))
        self._init_arm()

    def disconnect(self):
        """Disconnect the arm"""
        self.restore_to_default_position()
        if self.is_connected():
            self.interface.close()
            self.connected = False

    def _init_arm(self):
        """Initialize Arm."""
        self.restore_to_default_position()

    def degree_to_radian(self, angle_in_degree):
        """Convers angle unit degree to radian

        :param angle_in_degree: IP address
        :type angle_in_degree: float
        """
        return angle_in_degree * pi / 180.0

    def set_position_raw(self, pos_vector=None):
        """Move the arm to a known position vector
        :param pos_vector: position vector with angles (in degrees) for 6 servo motors
        :type pos_vector: tuple
        """
        # Check input position vector
        if len(pos_vector) != 6:
            raise self.EquipmentParameterError(f"wrong length of position vector: {len(pos_vector)}, should be 6")
        try:
            [int (i) for i in pos_vector]
        except ValueError as e_:
            raise self.EquipmentParameterError("Non integer position vector ?")
        # TODO: Find the angle limits and raise EquipmentParameterError if limits are crossed

        # Set to given position
        home_joint_angles_rad_str = str([self.degree_to_radian(angle) for angle in pos_vector])
        command_ = f"movej({home_joint_angles_rad_str}, a={self.joint_acceleration}, v={self.joint_speed}){self.newline_char}".encode()
        self.interface.send(command_)
        sleep(self.operation_settling_time)

    def restore_to_default_position(self):
        """Restore to default upright position."""
        self.set_position_raw((0, -90, 0, -90, 0, 0,))


if __name__ == "__main__":
    # Example run
    Arm = UR5("192.168.1.5")   # Connect to the serial port at COM13
    Arm.connect()         # Connect to the interface
    Arm.set_position_raw((0, -110, 0, -110, 0, 0,))
    Arm.disconnect()      # Free the port
