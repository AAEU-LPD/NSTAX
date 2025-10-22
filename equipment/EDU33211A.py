"""Equipment driver for the EDU33211A Waveform Generator.

Purpose of this module is to control an EDU33211A Waveform Generator as a test
equipment for specific singal generation related feature tests (Eg: control system for lab shaker).
"""

from time import sleep

from NSTA.equipment.equipment import Equipment
from NSTA.interface.pyvisa_interface import PyvisaInterface


class SignalGenerator(Equipment):
    def __init__(self):
        super().__init__("EDU33211A", version=0.1)
        self.interface = None


# [TODO]: add ranges/limits of all values
class EDU33211A(Equipment):
    """Equipment EDU33211A Waveform Generator.

    :param reset_enabled: enable or disable the factory resetiing of the device
    :type reset_enabled: bool
    """

    def __init__(self, reset_enabled=True, debug_logging=False):
        super().__init__("EDU33211A", version=0.1)
        self.interface = None
        self.reset_en = reset_enabled
        self.dbg_log = debug_logging

    def _check_interface(self):
        """Check if the specified port is available for connection

        :raises self.CouldNotConnectError: pyvisa connect error
        """
        try:
            self.interface.connect()
        except:
            raise self.CouldNotConnectError(
                "Error connecting to EDU33211A via pyvisa")
        self.interface.disconnect()

    def connect(self):
        """Connect to the device."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        self.interface = PyvisaInterface("EDU33211A")
        # Try to connect
        self.interface.connect()
        self._init_device()
        self.connected = True

    def disconnect(self):
        """Disconnect the device"""
        if self.reset_en:
            self.interface.device_reset()
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def _init_device(self):
        """Initialize device."""
        if self.reset_en:
            self.interface.device_reset()

    def set_wave_function(self, func):
        """
            Set the wave type from the following:
            "SIN", "SQU", "TRI", "RAMP", "PULS", "PRBS", "NOIS", "ARB", or "DC"

        :param func: the function type
        :type func: str
        """
        self.interface.write_data(f"FUNC {func}")

    def abort_operations(self):
        """
            Abort any operations running on the device
        """
        self.interface.write_data(f"ABOR")

    # FREQUENCY COMMANDS
    def set_frequency(self, freq):
        """Set the frequency of the wave

        :param freq: frequency value in Hz
        :type freq: int
        """
        self.interface.write_data(f"SOUR:FREQ {freq}")

    def measure_frequency(self):
        """Get the frequency value set in the device

        :return: frequency value in Hz
        :rtype: float
        """
        frequency = self.interface.read_data_ascii("SOUR:FREQ?")
        if self.dbg_log:
            self.logger.info("Frequency was "+str(frequency[0])+" Hz.")
        return frequency

    def set_phase_units(self, unit="DEG"):
        """Set the units for phase of the wave from the following:
          "DEG","RAD","SEC","DEF"

        :param unit: initials for the unit, defaults to "DEG"
        :type unit: str, optional
        """
        self.interface.write_data(f"UNIT:ANGL {unit}")

    def set_phase(self, phase):
        """Set the phase shift of the wave

        :param phase: phase value in set units
        :type phase: int
        """
        self.interface.write_data(f"SOUR:PHAS {phase}")

    # VOLTAGE COMMANDS
    # Voltage values
    def set_voltage(self, volt):
        """Set the voltage of the wave

        :param volt: voltage value in V
        :type volt: float
        """
        self.interface.write_data(f"SOUR:VOLT {volt}")

    def set_def_voltage(self):
        """Set the voltage to default value of the device
        """
        self.set_voltage(self, "DEF")

    def set_min_voltage(self):
        """Set the voltage to minimum value of the device
        """
        self.set_voltage(self, "MIN")

    def set_max_voltage(self):
        """Set the voltage to maximum value of the device
        """
        self.set_voltage(self, "MAX")

    def set_voltage_high(self, volt):
        """Set the voltage high value

        :param volt: voltage value in V
        :type volt: float
        """
        self.interface.write_data(f"SOUR:VOLT:HIGH {volt}")

    def set_voltage_low(self, volt):
        """Set the voltage low value

        :param volt: voltage value in V
        :type volt: float
        """
        self.interface.write_data(f"SOUR:VOLT:LOW {volt}")

    def set_offset(self, volt, unit="mV"):
        """Set the offset voltage value, and the units:
           "V" or "mV"

        :param volt: voltage value in V
        :type volt: float
        :param unit: units of the voltage offset, defaults to "mV"
        :type unit: str, optional
        """
        self.interface.write_data(f"SOUR:VOLT:OFFS {volt} {unit}")

    def set_voltage_limits(self, low, high):
        """Set the high and low limits of voltage for the device

        :param low: voltage low value in V
        :type low: float
        :param high: voltage high value in V
        :type high: float
        """
        self.interface.write_data(f"VOLT:LIM:HIGH {high}")
        self.interface.write_data(f"VOLT:LIM:LOW {low}")
        self.interface.write_data("VOLT:LIM:STAT ON")

    def measure_voltage(self):
        """Get the voltage value set in the device

        :return: voltage in V
        :rtype: float
        """
        voltage = self.interface.read_data_ascii("SOUR:VOLT?")
        if self.dbg_log:
            self.logger.info("Voltage was "+str(voltage[0])+" V.")
        return voltage

    # Voltage units
    def set_units_voltage_mode(self, unit="VPP"):
        """Set the voltage unit mode: "VPP" or "VRMS" or "DBM"

        :param unit: voltage unit mode, defaults to "VPP"
        :type unit: str, optional
        """
        self.interface.write_data(f"SOUR:VOLT:UNIT {unit}")

    def set_volt_unit_vpp(self):
        """Set voltage units to VPP
        """
        self.set_units_voltage_mode("VPP")

    def set_volt_unit_vrms(self):
        """Set voltage units to VRMS
        """
        self.set_units_voltage_mode("VRMS")

    def set_volt_unit_dbm(self):
        """Set voltage units to DBM
        """
        self.set_units_voltage_mode("DBM")

    def get_voltage_unit_mode(self):
        """Get the voltage units set in the device

        :return: voltage unit
        :rtype: str
        """
        unit = self.interface.read_data("SOUR:VOLT:UNIT?")
        if self.dbg_log:
            self.logger.info("Voltage units are "+str(unit)+".")
        return unit

    # GENERAL COMMANDS
    def enable_output(self):
        """Enable signal output from the device
        """
        self.interface.write_data("OUTP ON")

    def disable_output(self):
        """Disable signal output from the device
        """
        self.interface.write_data("OUTP OFF")

    def take_screenshot(self, path=""):
        """Take a screenshot of the display on the device (contains settings)

        :param path: path to save file, defaults to ""
        :type path: str, optional
        """
        # You can change the variable name and resource name
        f = open(f"{path}/screenshot.png", "wb")
        data = self.interface.read_data_raw("HCOP:SDUM:DATA?")
        # Returned data is prefixed with #nxxxxx where n is the number of bytes in
        # length field, xxxxxx is the bytes of data which is trailed by \n. Index
        # notation is used to drop the header and footer.
        f.write(data[(data[1]-46):-1])
        f.close()

    # CREATE SIGNALS
    def generate_sinwave(self, freq, volt, offset, phase, unit="mV"):
        """Generate a sin wave with the given parameters

        :param freq: frequency in Hz
        :type freq: float
        :param volt: voltage in V
        :type volt: float
        :param offset: voltage offset in given units
        :type offset: int
        :param phase: phase in degrees
        :type phase: int
        :param unit: voltage units, defaults to "mV"
        :type unit: str, optional
        """
        self.set_wave_function("SIN")
        self.set_voltage(volt)
        self.set_offset(offset/2, unit)
        self.set_frequency(freq)
        self.set_phase(phase)

    # Create sqwave
    def generate_squarewave_with_frequency(self, freq, volt, offset, duty_cycle, unit="mV"):
        """Generate a square wave with the given parameters

        :param freq: frequency in Hz
        :type freq: float
        :param volt: voltage in V
        :type volt: float
        :param offset: voltage offset in given units
        :type offset: int
        :param duty_cycle: duty cycle in percent
        :type duty_cycle: int (0-100)
        :param unit: voltage units, defaults to "mV"
        :type unit: str, optional
        """
        self.set_wave_function("SQU")
        self.set_voltage(volt)
        self.set_offset(offset/2, unit)
        self.set_frequency(freq)
        self.interface.write_data(f"FUNC:SQU:DCYC {duty_cycle}")

    def generate_squarewave_with_period(self, per, volt, offset, duty_cycle, unit="mV"):
        """Generate a square wave with the given parameters

        :param per: period in seconds (s)
        :type per: int
        :param volt: voltage in V
        :type volt: float
        :param offset: voltage offset in given units
        :type offset: int
        :param duty_cycle: duty cycle in percent
        :type duty_cycle: int (0-100)
        :param unit: voltage units, defaults to "mV"
        :type unit: str, optional
        """
        self.set_wave_function("SQU")
        self.set_voltage(volt)
        self.set_offset(offset/2, unit)
        self.interface.write_data(f"FUNC:SQU:PER {per}")
        self.interface.write_data(f"FUNC:SQU:DCYC {duty_cycle}")

    # Create rampwave
    def generate_rampwave(self, freq, volt, offset, symmetry=100, unit="mV"):
        """Generate a ramp wave with the given parameters

        :param freq: frequency in Hz
        :type freq: float
        :param volt: voltage in V
        :type volt: float
        :param offset: voltage offset in given units
        :type offset: int
        :param symmetry: wave symmetry (0-100), defaults to 100
        :type symmetry: int, optional
        :param unit:  voltage units, defaults to "mV"
        :type unit: str, optional
        """
        self.set_wave_function("RAMP")
        self.set_voltage(volt)
        self.set_offset(offset/2, unit)
        self.set_frequency(freq)
        self.interface.write_data(f"FUNC:RAMP:SYMM {symmetry}")

    # Create pulse
    def generate_pulsewave(self, freq, volt, offset, phase, width=100000, duty_cycle=10, lead_time=10, trail_time=10, unit="mV"):
        """Generate a custom pulse wave with the given parameters

        :param freq: frequency in Hz
        :type freq: float
        :param volt:  voltage in V
        :type volt: float
        :param offset: voltage offset in given units
        :type offset: int
        :param phase: phase in degrees
        :type phase: int
        :param width: signal width in ms, defaults to 100000
        :type width: int, optional
        :param duty_cycle: duty cycle in percent, defaults to 10
        :type duty_cycle: int, optional
        :param lead_time: leading time of pulse signal (upward ramp), defaults to 10
        :type lead_time: int, optional
        :param trail_time: trailing time of pulse signal (downward ramp), defaults to 10
        :type trail_time: int, optional
        :param unit: voltage units, defaults to "mV"
        :type unit: str, optional
        """
        self.set_wave_function("PULS")
        self.set_frequency(freq)
        self.set_voltage(volt)
        self.set_offset(offset/2, unit)
        self.set_phase(phase)
        self.interface.write_data(f"FUNC:PULS:WIDT {width} ms")
        self.interface.write_data(f"FUNC:PULS:DCYC {duty_cycle}")
        self.interface.write_data(f"FUNC:PULS:TRAN:LEAD {lead_time} ns")
        self.interface.write_data(f"FUNC:PULS:TRAN:TRA {trail_time} ns")


if __name__ == "__main__":
    ### SAMPLE WAVEFORM COMMAND FLOW ###
    signalgenerator = EDU33211A(reset_enabled=False)

    signalgenerator.connect()

    # signalgenerator.run_sample_sinwave()
    # signalgenerator.run_sample_squarewave()
    # signalgenerator.run_sample_rampwave()

    # signalgenerator.generate_sinwave(60, 2, 500, 30)
    # signalgenerator.generate_squarewave_with_frequency(100, 3, 1, 80, "V")
    # signalgenerator.generate_squarewave_with_period(0.001, 2, 0, 50, "V")
    # signalgenerator.generate_rampwave(1000, 2, 0, 25)
    # signalgenerator.generate_pulsewave(200000, 3, 0, 0, 0.003, 60, 40, 1000)

    signalgenerator.generate_sinwave(1, 0.1, 0, 0)
    signalgenerator.enable_output()
    sleep(1)

    signalgenerator.take_screenshot(path="../")
    print(signalgenerator.measure_frequency())
    print(signalgenerator.measure_voltage())
    print(signalgenerator.get_voltage_unit_mode())
    sleep(20)

    signalgenerator.disable_output()
    signalgenerator.disconnect()
