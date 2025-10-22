import time
import serial
from NSTA.equipment.AMARISOFT import AMARISOFT
from NSTA.equipment.NSTA25V import NSTA25V
from NSTA.equipment.NSTA25M import NSTA25M
from NSTA.interface.pyvisa_interface import PyvisaInterface

class hati_gps_test():
    def __init__(self, station, signal_generator_serial, amarisoft_ip):
        if station == "MAGNET":
            self.magnet = NSTA25M()
        elif station == "SHAKER":
            self.shaker = NSTA25V()
        self.gps = PyvisaInterface(signal_generator_serial)
        self.network = AMARISOFT(amarisoft_ip)
        
    def set_gps_region(self, region):
        valid_regions = ["munich", "brazil", "london", "ocean", "america","australia","mexico"]
        if region not in valid_regions:
            raise ValueError(f"Invalid region. Valid regions are: {valid_regions}")
        self.gps.connect()
        self.gps.write_data(f'SOUR:BB:GNSS:SETT:LOAD "{region}"')
        print(f"GPS region set to {region}")
        self.gps.write_data('SOUR:BB:GNSS:STAT ON')
        self.gps.disconnect()
        
    def set_gps_off(self):
        self.gps.connect()
        self.gps.write_data('SOUR:BB:GNSS:STAT OFF')
        print("GPS turned off")
        self.gps.disconnect()
        
    def set_network_band(self, cell_b20, cell_b2, gain_b20, gain_b2, action):
        self.network.connect()
        self.network.set_cell_gain(cell_b20, gain_b20)
        self.network.set_cell_gain(cell_b2, gain_b2)
        self.network.set_cell_gain("2", -100)
        self.network.disconnect()
        print(f"Successfully: {action}")

    def set_network_band_20(self, cell_b20, cell_b2):
        self.set_network_band(cell_b20, cell_b2, 0, -100, "set network band 20")

    def set_network_band_2(self, cell_b20, cell_b2):
        self.set_network_band(cell_b20, cell_b2, -100, 0, "set network band 2")

    def set_network_bands_none(self, cell_b20, cell_b2):
        self.set_network_band(cell_b20, cell_b2, -100, -100, "set network bands to None")

    def reset_network_bands(self, cell_b20, cell_b2):
        self.set_network_band(cell_b20, cell_b2, 0, 0, "reset network bands")
        
    def trigger_event(self,type="motion"):
        if type == "motion":
            self.activate_motion_event()
        elif type == "magnet":
            self.activate_magnet_event()
        else:
            raise ValueError("Invalid event type. Use 'motion' or 'magnet'.")
    
    def activate_motion_event(self):
        self.shaker.connect(auto_connect=True)
        msg = self.shaker.start_shaking()   # Start shaking at 150 RPM
        print(msg)                  # Print the reply from the shaker
        time.sleep(1*60)                   # Keep shaking for 60 seconds
        msg = self.shaker.stop_shaking()               # Stop shaking
        print(msg)                  # Print the reply from the shaker
        self.shaker.disconnect()
        
    def activate_magnet_event(self):
        self.magnet.connect(auto_connect=True)            # Connect to the interface
        msg = self.magnet.send_trigger()   # Start magnet at 150 RPM
        print(msg)                  # Print the reply from the Magnet
        time.sleep(10)                   # Keep magnet for 10 seconds
        # msg = self.magnet.stop_magnet()               # Stop magnet
        # print(msg)                  # Print the reply from the Magnet
        self.magnet.disconnect()         # Free the COM port
        
    # def activate_magnet_event(self):
    #     retries = 0
    #     while retries < 3:
    #         self.shaker.write(b'1')
    #         response = self.shaker.readline()
    #         if response.decode().strip() == "Received: 1":
    #             print(response.decode().strip())
    #             response = self.shaker.readline()
    #             if response.decode().strip() == "Triggering action for input '1'.":
    #                 print(response.decode().strip())
    #                 time.sleep(5)
    #                 response = self.shaker.readline()
    #                 if response.decode().strip() == "Finished Action":
    #                     print(response.decode().strip())
    #                     print("Successfully sent magnet downlink")
    #                     break
    #         retries += 1
    #         print("Failed to send magnet downlink. Trying Again...")
    #         time.sleep(2)
    
    def _send_message(self, message):
        self.shaker.write(message.encode())
        time.sleep(1)
        response = self.shaker.readlines()
        for line in response:
            print(line.decode().strip())
        return response
    
def _send_to_world(device):
    device.set_gps_off()
    device.reset_network_bands("5", "8")
    
def _send_to_australia(device):
    device.set_gps_region("australia")
    device.set_network_band_20("5", "8")
    
def _send_to_munich(device):
    device.set_gps_region("munich")
    device.set_network_band_20("5", "8")
    
def _send_to_london(device):
    device.set_gps_region("london")
    device.set_network_band_20("5", "8")
    
def _send_to_america(device):
    device.set_gps_region("america")
    device.set_network_band_2("5", "8")

def _send_to_brazil(device):
    device.set_gps_region("brazil")
    device.set_network_band_2("5","8")

def _send_to_mexico(device):
    device.set_gps_region("mexico")
    device.set_network_band_2("5","8")

def _send_to_ocean(device):
    device.set_gps_region("ocean")
    device.set_network_bands_none("5", "8")
    
def _run_region_sequence(device, regions, event_type="motion", repeats=1, wait_min=10):
    """
    Runs a sequence of region changes and triggers events.

    Args:
        device: The device object.
        regions: List of tuples (region_name, send_func), e.g. [("America", _send_to_america), ...]
        event_type: The event type to trigger ("motion" or "magnet").
        repeats: Number of times to trigger the event per region.
        wait_min: Minutes to wait between events.
    """
    for region_name, send_func in regions:
        print(f"Step: Changing region to {region_name}...")
        send_func(device)
        for i in range(repeats):
            print("Step time: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            device.trigger_event(event_type)
            time.sleep(wait_min * 60)
        
def start_test_check_band_priorities(device):
    REPEATS = 3
    DL_WAIT_MIN = 10
    print("test_start_time: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    expected_end_time = time.localtime(time.time() + (DL_WAIT_MIN * REPEATS * 6))
    print("test_end_time: ", time.strftime("%Y-%m-%d %H:%M:%S", expected_end_time))
    
    # Example usage:
    region_sequence = [
        ("America", _send_to_america),
        ("Munich", _send_to_munich),
        ("Mexico", _send_to_mexico),
        ("Australia", _send_to_australia),
        ("Brazil", _send_to_brazil),
        ("London", _send_to_london),
    ]
    _run_region_sequence(device, region_sequence, event_type="motion", repeats=3, wait_min=DL_WAIT_MIN)
    

def start_test_check_brazil_profile(device):
    DL_WAIT_MIN = 15
    print("test_start_time: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    expected_end_time = time.localtime(time.time() + (DL_WAIT_MIN * 60 * 7))
    print("test_end_time: ", time.strftime("%Y-%m-%d %H:%M:%S", expected_end_time))

    region_sequence = [
        ("Brazil", _send_to_brazil),
        ("Brazil", _send_to_brazil),
        ("Ocean", _send_to_ocean),
        ("Munich", _send_to_munich),
        ("Brazil", _send_to_brazil),
        ("Brazil", _send_to_brazil),
    ]
    _run_region_sequence(device, region_sequence, event_type="motion", repeats=1, wait_min=DL_WAIT_MIN)
    
def start_test_check_munich_profile(device):
    DL_WAIT_MIN = 15
    print("test_start_time: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
    expected_end_time = time.localtime(time.time() + (DL_WAIT_MIN * 60 * 7))
    print("test_end_time: ", time.strftime("%Y-%m-%d %H:%M:%S", expected_end_time))

    region_sequence = [
        ("Munich", _send_to_munich),
        ("Ocean", _send_to_ocean),
        ("Brazil", _send_to_brazil),
        ("Munich", _send_to_munich),
        ("Munich", _send_to_munich),
    ]
    # The first region ("Munich") should trigger event once, then each subsequent region triggers once,
    # except the last "Munich" which triggers twice (to match the original logic).
    # We'll use repeats=1 for all, then call trigger_event and sleep again after the last step.
    _run_region_sequence(device, region_sequence[:-1], event_type="motion", repeats=1, wait_min=DL_WAIT_MIN)
    # For the last "Munich", trigger twice with wait in between
    for _ in range(2):
        print("Step: Changing region to Munich...")
        _send_to_munich(device)
        device.trigger_event("motion")
        print("Step time: ", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
        time.sleep(DL_WAIT_MIN * 60)


if __name__ == "__main__":
    # MOVEMENT_TIMEOUT_MIN = 30
    DL_WAIT_MIN = 5 
    
    mydevice = hati_gps_test("SHAKER","SMBV100B", "10.51.16.6")
    # mydevice.activate_magnet_event()
    # mydevice.set_network_band_20("5","8")
    # time.sleep(10)
    # mydevice.set_network_band_2("5","8")
    # time.sleep(10)
    # mydevice.set_network_bands_none("5","8")
    # time.sleep(10)
    # mydevice.reset_network_bands("5","8")
    # mydevice.set_gps_region("munich")
    # mydevice.set_gps_region("brazil")
    # mydevice.set_gps_region("ocean")
    
    ### TEST###
    # _send_to_brazil(mydevice)
    # _send_to_munich(mydevice)
    # _send_to_ocean(mydevice)
    # mydevice.activate_magnet_event()
    # start_test_check_brazil_profile(mydevice)
    # start_test_check_munich_profile(mydevice)
    start_test_check_band_priorities(mydevice)
    # mydevice.set_gps_off()
