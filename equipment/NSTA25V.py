from time import sleep
import serial.tools.list_ports

from NSTAX.equipment.equipment import Equipment
from NSTAX.interface.rs232_interface import RS232Interface

SPEED_LEVEL_HIGH = 4   # High speed level for the shaker
SPEED_LEVEL_MEDIUM = 3    # Medium speed level for the shaker
SPEED_LEVEL_LOW = 2   # Low speed level for the shaker
SPEED_LEVEL_STOP = 0   # Stop speed level for the shaker
SYSTEM_RESET = -1   # System reset command for the shaker

class NSTA25V(Equipment):
    """Equipment class for Nanostation 2025 Vibration Shaker.

    :param port: COM port for the shaker unit
    :type port: str
    """

    def __init__(self, port=None):
        super().__init__("NSTA25V", version=0.1)
        self.interface = None
        self.port = port        # COM port for the Shaker

    def connect(self,auto_connect=False):
        """Connect to the shaker."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        if not auto_connect:
            self.interface = RS232Interface(self.port, baudrate=9600, EOL="\n")
            try:
                self.interface.connect()
                found = self._verify_station()
                if not found:
                    raise self.CouldNotConnectError("Could not find a valid port for the Shaker.")
            except Exception:
                raise self.CouldNotConnectError("Could not connect to the specified port")
        else:
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            found = False
            for port in available_ports:
                print(f"Trying to connect to port: {port}")
                self.interface = RS232Interface(port, baudrate=9600, EOL="\n")
                try:
                    self.interface.connect()
                    found = self._verify_station()
                    if not found:
                        self.interface.disconnect()
                    else:
                        break
                except Exception:
                    raise self.CouldNotConnectError("Could not find a valid port for the Shaker.")
        self.connected = True
        
    def _verify_station(self):
        """Verify if the Shaker is connected and responding."""
        msg = self.reset_device()
        msg = msg.strip()
        station_id = msg.split()[0] if msg else ""
        if not msg.startswith("NANOSTATION_V"):
            print(f"Shaker did not respond correctly. Expected 'NANOSTATION_V' but got: '{station_id}'")
            return False
        print("Shaker connected successfully. ID:", station_id)
        return True

    def disconnect(self):
        """Disconnect the shaker"""
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def start_shaking(self, set_speed=SPEED_LEVEL_HIGH):
        """Start shaking over a given speed"""
        cmd = f"{set_speed}"
        self.interface.write_data(cmd)
        sleep(1)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply

    def stop_shaking(self):
        """Stop shaking"""
        cmd = f"{SPEED_LEVEL_STOP}"
        self.interface.write_data(cmd)
        sleep(1)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply

    def reset_device(self):
        """Reset the device"""
        print("Resetting the shaker...")
        cmd = f"{SYSTEM_RESET}"
        self.interface.write_data(cmd)
        sleep(2)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply


if __name__ == "__main__":
    shake_min = 1
    # Example run
    Shaker = NSTA25V("/dev/ttyUSB0")   # Connect to the serial port at COM6
    Shaker.connect()            # Connect to the interface
    msg = Shaker.start_shaking()   # Start shaking at 150 RPM
    print(msg)                  # Print the reply from the shaker
    sleep(shake_min*60)                   # Keep shaking for 60 seconds
    msg = Shaker.stop_shaking()               # Stop shaking
    print(msg)                  # Print the reply from the shaker
    Shaker.disconnect()         # Free the COM port
