from time import sleep
import serial.tools.list_ports

from NSTA.equipment.equipment import Equipment
from NSTA.interface.rs232_interface import RS232Interface

MAGNET_TRIGGER_ON = 1  # Magnet trigger on command
MAGNET_TRIGGER_OFF = 0  # Magnet trigger off command
SYSTEM_RESET = -1   # System reset command for the station

class NSTA25M(Equipment):
    """Equipment class for Nanostation 2025 Magnet .

    :param port: COM port for the magnet unit
    :type port: str
    """

    def __init__(self, port=None):
        super().__init__("NSTA25M", version=0.1)
        self.interface = None
        self.port = port        # COM port for the Magnet

    def connect(self,auto_connect=False):
        """Connect to the Magnet."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        if not auto_connect:
            self.interface = RS232Interface(self.port, baudrate=9600, EOL="\n")
            try:
                self.interface.connect()
                found = self._verify_station()
                if not found:
                    raise self.CouldNotConnectError("Could not find a valid port for the Magnet.")
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
                    raise self.CouldNotConnectError("Could not find a valid port for the Magnet.")
        self.connected = True
        
    def _verify_station(self):
        """Verify if the Magnet is connected and responding."""
        msg = self.reset_device()
        msg = msg.strip()
        station_id = msg.split()[0] if msg else ""
        if not msg.startswith("NANOSTATION_M"):
            print(f"Magnet did not respond correctly. Expected 'NANOSTATION_M' but got: '{station_id}'")
            return False
        print("Magnet connected successfully. ID:", station_id)
        return True

    def disconnect(self):
        """Disconnect the Magnet"""
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def send_trigger(self, set_speed=MAGNET_TRIGGER_ON):
        """Trigger magnet for 10 seconds"""
        cmd = f"{set_speed}"
        self.interface.write_data(cmd)
        sleep(1)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply

    def stop_magnet(self):
        """Stop the magnet"""
        cmd = f"{MAGNET_TRIGGER_OFF}"
        self.interface.write_data(cmd)
        sleep(1)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply

    def reset_device(self):
        """Reset the device"""
        print("Resetting the Magnet...")
        cmd = f"{SYSTEM_RESET}"
        self.interface.write_data(cmd)
        sleep(2)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply


if __name__ == "__main__":
    # Example run
    Magnet = NSTA25M("/dev/ttyUSB2")   # Connect to the serial port at COM6
    Magnet.connect(auto=True)            # Connect to the interface
    # msg = Magnet.send_trigger()   # Start magnet at 150 RPM
    # print(msg)                  # Print the reply from the Magnet
    # sleep(10)                   # Keep magnet for 10 seconds
    # msg = Magnet.stop_magnet()               # Stop magnet
    # print(msg)                  # Print the reply from the Magnet
    Magnet.disconnect()         # Free the COM port
