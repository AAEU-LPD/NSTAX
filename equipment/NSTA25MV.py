from time import sleep
import serial.tools.list_ports

from NSTA.equipment.equipment import Equipment
from NSTA.interface.rs232_interface import RS232Interface

MAGNET_A_TRIGGER_ON = 20  # Magnet trigger on command
MAGNET_A_TRIGGER_OFF = 21  # Magnet trigger off command
MAGNET_B_TRIGGER_ON = 30  # Magnet trigger on command
MAGNET_B_TRIGGER_OFF = 31  # Magnet trigger off command
SPEED_A_LEVEL_HIGH = 3   # High speed level for the shaker
SPEED_A_LEVEL_MEDIUM = 2    # Medium speed level for the shaker
SPEED_A_LEVEL_LOW = 1   # Low speed level for the shaker
SPEED_A_LEVEL_STOP = 0   # Stop speed level for the shaker
SPEED_B_LEVEL_HIGH = 13   # High speed level for the shaker
SPEED_B_LEVEL_MEDIUM = 12    # Medium speed level for the shaker
SPEED_B_LEVEL_LOW = 11   # Low speed level for the shaker
SPEED_B_LEVEL_STOP = 10   # Stop speed level for the shaker
SYSTEM_RESET = -1   # System reset command for the shaker

class NSTA25MV(Equipment):
    """Equipment class for Nanostation 2025 Magnet + Shaker .

    :param port: COM port for the magnet unit
    :type port: str
    """

    def __init__(self, port=None, auto_connect=True):
        super().__init__("NSTA25MV", version=0.1)
        self.interface = None
        self.port = port        # COM port for the Magnet
        self.auto_connect = auto_connect

    def connect(self):
        """Connect to the station."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        if not self.auto_connect:
            self.interface = RS232Interface(self.port, baudrate=9600, EOL="\n")
            try:
                self.interface.connect()
                found = self._verify_station()
                if not found:
                    raise self.CouldNotConnectError("Could not find a valid port for the Station.")
            except Exception:
                raise self.CouldNotConnectError("Could not connect to the specified port")
        else:
            available_ports = [port.device for port in serial.tools.list_ports.comports()]
            found = False
            for port in available_ports:
                self.logger.info(f"Trying to connect to port: {port}")
                self.interface = RS232Interface(port, baudrate=9600, EOL="\n")
                try:
                    self.interface.connect()
                    found = self._verify_station()
                    if not found:
                        self.interface.disconnect()
                    else:
                        break
                except Exception:
                    raise self.CouldNotConnectError("Could not find a valid port for the Station.")
        self.connected = True
        
    def _verify_station(self):
        """Verify if the Station is connected and responding."""
        msg = self.reset_device()
        msg = msg.strip()
        station_id = msg.split()[0] if msg else ""
        if not msg.startswith("NANOSTATION_MV"):
            self.logger.info(f"Station did not respond correctly. Expected 'NANOSTATION_MV' but got: '{station_id}'")
            return False
        self.logger.info(f"Station connected successfully. ID: {station_id}")
        return True

    def disconnect(self):
        """Disconnect the Magnet"""
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def send_trigger(self, trigger_value, response_time=1):
        """Trigger magnet for 10 seconds"""
        cmd = f"{trigger_value}"
        self.interface.write_data(cmd)
        sleep(response_time)  # Wait for the command to be processed
        reply = self.interface.read_data(cmd)
        return reply

    def start_magnet(self, magnet_type):
        """Start the magnet. A timeout will only keep the magnet ON for 10 seconds before it turns off"""
        if magnet_type == 'A':
            MAGNET_TRIGGER_ON = MAGNET_A_TRIGGER_ON
        elif magnet_type == 'B':
            MAGNET_TRIGGER_ON = MAGNET_B_TRIGGER_ON
        else:
            raise ValueError("Invalid magnet type. Use 'A' or 'B'.")
        return self.send_trigger(MAGNET_TRIGGER_ON, response_time=1)

    def stop_magnet(self, magnet_type):
        """Stop the magnet"""
        if magnet_type == 'A':
            MAGNET_TRIGGER_OFF = MAGNET_A_TRIGGER_OFF
        elif magnet_type == 'B':
            MAGNET_TRIGGER_OFF = MAGNET_B_TRIGGER_OFF
        else:
            raise ValueError("Invalid magnet type. Use 'A' or 'B'.")
        return self.send_trigger(MAGNET_TRIGGER_OFF, response_time=1)
    
    def start_shaking(self, motor_type, set_speed='HIGH'):
        """Start shaking over a given speed"""
        if motor_type == 'A':
            if set_speed == 'HIGH':
                set_speed = SPEED_A_LEVEL_HIGH 
            elif set_speed == 'MEDIUM':
                set_speed = SPEED_A_LEVEL_MEDIUM 
            elif set_speed == 'LOW':
                set_speed = SPEED_A_LEVEL_LOW 
            else:
                raise ValueError("Invalid speed level. Use 'HIGH', 'MEDIUM', or 'LOW'.")
        elif motor_type == 'B':
            if set_speed == 'HIGH':
                set_speed = SPEED_B_LEVEL_HIGH 
            elif set_speed == 'MEDIUM':
                set_speed = SPEED_B_LEVEL_MEDIUM 
            elif set_speed == 'LOW':
                set_speed = SPEED_B_LEVEL_LOW 
            else:
                raise ValueError("Invalid speed level. Use 'HIGH', 'MEDIUM', or 'LOW'.")
        else:
            raise ValueError("Invalid motor type. Use 'A' or 'B'.")
        return self.send_trigger(set_speed, response_time=1)

    def stop_shaking(self, motor_type):
        """Stop shaking"""
        if motor_type == 'A':
            set_speed = SPEED_A_LEVEL_STOP
        elif motor_type == 'B':
            set_speed = SPEED_B_LEVEL_STOP
        else:
            raise ValueError("Invalid motor type. Use 'A' or 'B'.")
        return self.send_trigger(set_speed, response_time=1)

    def reset_device(self):
        """Reset the device"""
        self.logger.info("Resetting the Station...")
        return self.send_trigger(SYSTEM_RESET, response_time=2)


if __name__ == "__main__":
    # Example run
    Station = NSTA25MV(auto_connect=True)   # Connect to the serial port at COM6
    Station.connect()            # Connect to the interface
    msg = Station.start_shaking(motor_type='B')   # Start magnet at 150 RPM
    print(msg)                  # Print the reply from the Magnet
    sleep(30)                   # Keep magnet for 30 seconds
    msg = Station.stop_shaking(motor_type='B')               # Stop magnet
    print(msg)                  # Print the reply from the Station
    # msg = Station.start_magnet(magnet_type='B')   # Start magnet at 150 RPM
    # print(msg)                  # Print the reply from the Magnet
    # sleep(12)
    # msg = Station.start_magnet(magnet_type='A')   # Start magnet at 150 RPM
    # print(msg)                  # Print the reply from the Magnet
    # sleep(12)
    Station.disconnect()         # Free the COM port
    
