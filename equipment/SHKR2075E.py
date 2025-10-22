""" Equipment driver for the 2075E Shaker that uses a waveform generator.

    Purpose of this module is to control an 2075E Shaker with its amplifier module.
    A Waveform Generator is required to send the output signal to the amplifier.

    :raises Exception: Waveform Generator not connected or Incorrect Serial Number
"""
from time import sleep
from threading import Thread

from NSTA.equipment.equipment import Equipment
from NSTA.equipment.EDU33211A import EDU33211A


class SHKR2075E(Equipment):
    def __init__(self, waveform_generator, reset_enabled=False, debug_logging=False):
        """Equipment 2075E Shaker and Amplifier control.

        :param waveform_generator: serial number of the waveform generator to use
        :type waveform_generator: string
        :param reset_enabled: factory reset py-visa device before using, defaults to True
        :type reset_enabled: bool, optional
        :param debug_logging: enabled console logs, defaults to False
        :type debug_logging: bool, optional
        :raises Exception: If waveform generator is not connected. This exception will be raised
        """
        super().__init__("SHKR2075E", version=0.1)
        self.interface = None
        if waveform_generator == "EDU33211A":
            self.signalgenerator = EDU33211A(reset_enabled=False)
        else:
            raise Exception("Waveform generator with this Serial not found!.")

    def connect(self):
        """Connect to the signal generator to control the amplifier input
        """
        self.signalgenerator.connect()

    def disconnect(self):
        """Disconnect from the signal generator
        """
        self.signalgenerator.disconnect()

    def enable_output(self):
        """Enable the output from the signal generator
        """
        self.signalgenerator.enable_output()

    def disable_output(self):
        """Disable the output from the signal generator
        """
        self.signalgenerator.disable_output()

    def send_output(self, freq, voltage, duration):
        """Send a sine wave output at the specified frequency, voltage and duration

        :param freq: Frequency in Hz (1Hz-100Hz)
        :type freq: int
        :param voltage: Voltage in Volts (0.01V - 0.30V)
        :type voltage: float
        :param duration: Time in Seconds (5s - 900s[15 min])
        :type duration: int
        """
        upper_frequency_limit = 1000
        lower_frequency_limit = 1
        upper_voltage_limit = 0.40
        lower_voltage_limit = 0.01
        min_duration = 5
        max_duration = 900

        if freq > upper_frequency_limit:
            freq = upper_frequency_limit
        if freq < lower_frequency_limit:
            freq = upper_frequency_limit
        if voltage > upper_voltage_limit:
            voltage = upper_voltage_limit
        if voltage < lower_voltage_limit:
            voltage = lower_voltage_limit
        if duration > max_duration:
            duration = max_duration
        if duration < min_duration:
            duration = min_duration

        self.signalgenerator.generate_sinwave(freq, voltage, 0, 0)
        self.signalgenerator.enable_output()
        sleep(duration)
        self.signalgenerator.disable_output()
        
    def send_output_threaded(self, freq, voltage, duration, delay_start=False):
        """Send a sine wave output at the specified frequency, voltage and duration

        :param freq: Frequency in Hz (1Hz-100Hz)
        :type freq: int
        :param voltage: Voltage in Volts (0.01V - 0.30V)
        :type voltage: float
        :param duration: Time in Seconds (5s - 900s[15 min])
        :type duration: int
        """   
        self.output_thread = Thread(target=self.send_output, args=(freq,voltage,duration))
        self.output_thread.start()
        
    def wait_for_thread_finish(self):
        self.output_thread.join()
        
    def send_output_manual(self, freq, voltage):
        """Send a sine wave output manually at the specified frequency, voltage and duration.

        Output enable/disable, and delay time function is required before and after this is called.

        :param freq: Frequency in Hz (1Hz-100Hz)
        :type freq: int
        :param voltage: Voltage in Volts (0.01V - 0.30V)
        :type voltage: float
        :param duration: Time in Seconds (5s - 900s[15 min])
        :type duration: int
        """
        upper_frequency_limit = 100
        lower_frequency_limit = 1
        upper_voltage_limit = 0.30
        lower_voltage_limit = 0.01

        if freq > upper_frequency_limit:
            freq = upper_frequency_limit
        if freq < lower_frequency_limit:
            freq = upper_frequency_limit
        if voltage > upper_voltage_limit:
            voltage = upper_voltage_limit
        if voltage < lower_voltage_limit:
            voltage = lower_voltage_limit

        self.signalgenerator.generate_sinwave(freq, voltage, 0, 0)


if __name__ == "__main__":
    ### SAMPLE SHAKER COMMAND FLOW ###
    shaker = SHKR2075E("EDU33211A")
    shaker.connect()
    shaker.send_output(10, 0.1, 5)
    shaker.disconnect()
