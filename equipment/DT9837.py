"""Equipment driver for the Digilent DT9837 signal analyzer.
The Purpose of this module is to measure voltage readings from a connected sensor
or to output waveforms from the equipment.
"""

from threading import Thread
from queue import Queue
from ctypes import *
import csv

from NSTAX.equipment.equipment import Equipment

# Config Params
NUM_CHANNELS = 4  # Max 4 channels for DT9837
ALL_CHANNEL_GAIN = 1  # 1 or 10
CLOCK_FREQUENCY = 1000.0  # Max: 46875Hz (output), 52700Hz (input)

CHANNEL_GAIN_0 = 1  # Z (1 or 10)
CHANNEL_GAIN_1 = 1  # Y (1 or 10)
CHANNEL_GAIN_2 = 1  # X (1 or 10)
CHANNEL_GAIN_3 = 1  # DAC (1 or 10)

WAVEFORM_AMPLITUDE = 3  # in volts (V) [0V-10V]
WAVEFORM_FREQUENCY = 10  # in hertz (Hz) [10Hz-400Hz]
WAVEFORM_DURATION = 10  # in seconds (s)

# Error Codes
ERR_CFG_FAILURE = -1
ERR_CFG_SUCCESS = 0
ERR_INIT_CONFIG = 1
ERR_BOARD_CONFIG = 2
ERR_CHANNEL_CONFIG = 3
ERR_DATA_CONFIG = 4
ERR_MEASUREMENT = 5
ERR_OUTPUT = 6
ERR_DEINIT_CONFIG = 7


class DT9837(Equipment):
    def __init__(self, path=""):
        """Equipment class for DT9837 signal analyzer
        """
        super().__init__("DT9837", version=0.1)
        self.interface = None
        # self.dt_lib = CDLL(f"{NSTA_PATH}\static\signal_analysis\dt9837_lib.so")
        dll_path = path + "static/signal_analysis/dt9837_lib.so"
        self.dt_lib = CDLL(f"{dll_path}")

    def connect(self):
        """Connect to the device."""
        # Disconnect if busy
        if self.is_connected():
            self.disconnect()
        err_str = ""
        self.init = self.dt_lib.initialize_board
        err_code = self.init()
        if err_code != 0:
            err_str = "ERROR_INIT_CONFIG_FAILURE"
            self.logger.info(
                f"Error Occured: Board not connected! Code:{err_code}_{err_str}")
            raise Exception(
                f"Error Occured: Board not connected! Code:{err_code}_{err_str}")
        self.connected = True

    def disconnect(self):
        """Disconnect the device"""
        if self.is_connected():
            err_str = ""
            self.deinit = self.dt_lib.deinit_board
            err_code = self.deinit()
            if err_code != 0:
                err_str = "ERROR_DEINIT_CONFIG_FAILURE"
                self.logger.info(f"Error Occured: {err_code}_{err_str}")
                raise Exception(f"Error Occured: {err_code}_{err_str}")
        self.connected = False

    def measure_acceleration_to_queue(self, duration, result_queue):
        """This function measures the acceleration reading

        A 3 axis accelerometer must be connected to the equipment.
        Measurment can be recorded indefinately until keyboard interrupt or can be timed in seconds

        :param duration: time in seconds(s) of the output signal
        :type duration: int
        :param timer_enabled: enable timed output, defaults to True
        :type timer_enabled: bool, optional
        :param use_default_vals: use the set default values of the equipment, defaults to True
        :type use_default_vals: bool, optional
        :param save_csv: save the output to a csv file, defaults to False
        :type use_default_vals: bool, optional
        """
        # C Functions assignment
        self.measure = self.dt_lib.measure
        self.get_data = self.dt_lib.get_channel_data
        self.cleanup_data = self.dt_lib.cleanup_data
        # C Argument types assignment
        self.measure.argtypes = [c_bool, c_int, c_float,
                                 c_int, c_int, c_int, c_int, c_int, c_bool, c_int]
        # C Return types assignment
        self.measure.restype = c_int
        self.get_data.restype = ChannelData
        # Measurement Excecution
        self.logger.info(
            f"[Signal Analyzer]: Measurement Started for {duration} seconds")
        print(f"[Signal Analyzer]: Measurement Started for {duration} seconds")
        err_code = self.measure(True, NUM_CHANNELS,
                                CLOCK_FREQUENCY, ALL_CHANNEL_GAIN, CHANNEL_GAIN_0, CHANNEL_GAIN_1, CHANNEL_GAIN_2, CHANNEL_GAIN_3, True, duration)
        self._error_check(err_code)
        if err_code != ERR_CFG_SUCCESS:
            raise Exception("[Signal Analyzer]:Error - Measurement failed!")
        # Acquiring the stored data
        data_struct = self.get_data()
        channels = [[round(data_struct.channel[i][j], 3)
                     for j in range(data_struct.num_readings)] for i in range(4)]
        time_ms = [round(data_struct.time_ms[i], 3)
                   for i in range(data_struct.num_readings)]

        # Free the memory allocated
        self.cleanup_data()

        print(f"Sending to queue")
        result_queue.put([time_ms, channels])

    def measure_acceleration(self, duration, timer_enabled=True, use_default_vals=True, save_csv=False):
        """This function measures the acceleration reading

        A 3 axis accelerometer must be connected to the equipment.
        Measurment can be recorded indefinately until keyboard interrupt or can be timed in seconds

        :param duration: time in seconds(s) of the output signal
        :type duration: int
        :param timer_enabled: enable timed output, defaults to True
        :type timer_enabled: bool, optional
        :param use_default_vals: use the set default values of the equipment, defaults to True
        :type use_default_vals: bool, optional
        :param save_csv: save the output to a csv file, defaults to False
        :type use_default_vals: bool, optional
        """
        # C Functions assignment
        self.measure = self.dt_lib.measure
        self.get_data = self.dt_lib.get_channel_data
        self.cleanup_data = self.dt_lib.cleanup_data
        # C Argument types assignment
        self.measure.argtypes = [c_bool, c_int, c_float,
                                 c_int, c_int, c_int, c_int, c_int, c_bool, c_int]
        # C Return types assignment
        self.measure.restype = c_int
        self.get_data.restype = ChannelData
        # Measurement Excecution
        self.logger.info(
            f"[Signal Analyzer]: Measurement Started for {duration} seconds")
        err_code = self.measure(use_default_vals, NUM_CHANNELS,
                                CLOCK_FREQUENCY, ALL_CHANNEL_GAIN, CHANNEL_GAIN_0, CHANNEL_GAIN_1, CHANNEL_GAIN_2, CHANNEL_GAIN_3, timer_enabled, duration)
        self._error_check(err_code)
        if err_code != ERR_CFG_SUCCESS:
            raise Exception("[Signal Analyzer]:Error - Measurement failed!")
        # Acquiring the stored data
        data_struct = self.get_data()
        channels = [[round(data_struct.channel[i][j], 3)
                     for j in range(data_struct.num_readings)] for i in range(4)]
        time_ms = [round(data_struct.time_ms[i], 3)
                   for i in range(data_struct.num_readings)]

        # Free the memory allocated
        self.cleanup_data()

        return time_ms, channels

    def measure_acceleration_threaded(self, duration):
        """Starts a threaded measurement of acceleration data.

        This method launches a background thread to measure acceleration from a connected 3-axis accelerometer
        for the specified duration. Results are placed in a queue for later retrieval.

        :param duration: Measurement duration in seconds.
        :type duration: int
        """
        self.result_queue = Queue()
        self.measure_thread = Thread(target=self.measure_acceleration_to_queue, args=(duration, self.result_queue))
        self.measure_thread.start()

    def wait_for_thread_finish(self):
        """Waits for the measurement thread to finish and retrieves the results.
        
        :return: Tuple containing time values and channel data.
        :rtype: tuple
        """
        self.measure_thread.join()
        print("Joined")
        while not self.result_queue.empty():
            res_arr = self.result_queue.get()
            print(res_arr)

        time_ms, channels = res_arr[0], res_arr[1]

        return time_ms, channels

    def generate_squarewave(self, duration, timer_enabled=True, use_default_vals=True, read_input=True):
        """This function generates a simple squarewave

        Generates a wave at the specified amplitude (V), frequency (Hz) and duration (in s).
        The function can be configured to record the output signal on channel 4 of the analog inputs.

        :param duration: time in seconds(s) of the output signal
        :type duration: int
        :param timer_enabled: enable timed output, defaults to True
        :type timer_enabled: bool, optional
        :param use_default_vals: use the set default values of the equipment, defaults to True
        :type use_default_vals: bool, optional
        :param read_input: record the input into a csv, defaults to True
        :type read_input: bool, optional
        """
        # C Functions assignment
        self.generate = self.dt_lib.generate
        self.get_data = self.dt_lib.get_channel_data
        self.cleanup_data = self.dt_lib.cleanup_data
        # C Argument types assignment
        self.generate.argtypes = [
            c_bool,  c_bool, c_float, c_int, c_int, c_int, c_bool, c_int]
        # C Return types assignment
        self.generate.restype = c_int
        self.get_data.restype = ChannelData
        # Measurement Excecution
        if timer_enabled:
            self.logger.info(
                f"[Signal Analyzer]: Squarewave Output for {duration} seconds. Read_Input {read_input}")
        else:
            self.logger.info(
                f"[Signal Analyzer]: Squarewave Output till keypress. Read_Input {read_input}")
        err_code = self.generate(use_default_vals, read_input, CLOCK_FREQUENCY, ALL_CHANNEL_GAIN,
                                 WAVEFORM_AMPLITUDE, WAVEFORM_FREQUENCY, timer_enabled, duration)
        self._error_check(err_code)
        if err_code != ERR_CFG_SUCCESS:
            raise Exception(
                "[Signal Analyzer]: Error - Output generation failed!")
        if read_input:
            # Acquiring the stored data
            data_struct = self.get_data()
            channels = [[round(data_struct.channel[i][j], 3)
                        for j in range(data_struct.num_readings)] for i in range(4)]
            time_ms = [round(data_struct.time_ms[i], 3)
                       for i in range(data_struct.num_readings)]

            # Free the memory allocated
            self.cleanup_data()

            return time_ms, channels
        else:
            return ERR_CFG_SUCCESS, ERR_CFG_SUCCESS

    def save_measurement_to_csv(self, time_vals, sensor_vals, filename="", suffix=""):
        """Saves the measurement data to a CSV file.
        
        :param time_vals: List of time values in milliseconds.
        :type time_vals: list
        :param sensor_vals: 2D list of sensor values for each channel.
        :type sensor_vals: list
        :param filename: Base filename for the CSV file, defaults to "".
        :type filename: str, optional
        :param suffix: Suffix to append to the filename, defaults to "".
        :type suffix: str, optional
        """
        csv_file = f"{filename}AXL_sensor_data{suffix}.csv"
        # Write to CSV
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)

            # Write headers
            writer.writerow(["time(s)", "accel_x(g)", "accel_y(g)", "accel_z(g)", "DAC(V)"])

            # Write data
            for i in range(len(time_vals)):
                writer.writerow([time_vals[i], sensor_vals[0][i], sensor_vals[1][i], sensor_vals[2][i], sensor_vals[3][i]])

    def _error_check(self, err_code):
        """Represents the different error codes that occur from the shared .so library

        Prints out the error output in case of errors.

        :param err_code: the error code (from definitions in file)
        :type err_code: int
        """
        err_str = ""
        if err_code != ERR_CFG_SUCCESS:
            if err_code == ERR_CFG_FAILURE:
                err_str = "ERROR_MISC_FAILURE"
            if err_code == ERR_INIT_CONFIG:
                err_str = "ERROR_INIT_CONFIG_FAILURE"
            if err_code == ERR_BOARD_CONFIG:
                err_str = "ERROR_BOARD_CONFIG_FAILURE"
            if err_code == ERR_CHANNEL_CONFIG:
                err_str = "ERROR_CHANNEL_CONFIG_FAILURE"
            if err_code == ERR_DATA_CONFIG:
                err_str = "ERROR_DATA_CONFIG_FAILURE"
            if err_code == ERR_MEASUREMENT:
                err_str = "ERROR_MEASUREMENT_FAILURE"
            if err_code == ERR_OUTPUT:
                err_str = "ERROR_OUTPUT_FAILURE"
            if err_code == ERR_DEINIT_CONFIG:
                err_str = "ERROR_DEINIT_CONFIG_FAILURE"
            self.logger.info(f"Error Occured: {err_code}_{err_str}")


class ChannelData(Structure):
    _fields_ = [
        ("channel", (POINTER(c_double)) * NUM_CHANNELS),
        ("time_ms", POINTER(c_double)),
        ("num_readings", c_int),
        ("max_readings", c_int)
    ]


if __name__ == "__main__":
    signalanalyzer = DT9837()

    signalanalyzer.connect()
    time_vals, sensor_vals = signalanalyzer.measure_acceleration(
        2, timer_enabled=True, save_csv=True)
    # time_vals, sensor_vals = signalanalyzer.generate_squarewave(
    #     0, timer_enabled=False, use_default_vals=False)

    # Print the data (DEBUGGING)
    print("\n### DATA(first and last two values) ###\nTime(ms),accel_x(g),accel_y(g),accel_z(g)")
    print(
        f"{time_vals[0]},{sensor_vals[0][0]},{sensor_vals[1][0]},{sensor_vals[2][0]},{sensor_vals[3][0]}")
    print(
        f"{time_vals[1]},{sensor_vals[0][1]},{sensor_vals[1][1]},{sensor_vals[2][1]},{sensor_vals[3][1]}")
    print(
        f"{time_vals[-1]},{sensor_vals[0][-1]},{sensor_vals[1][-1]},{sensor_vals[2][-1]},{sensor_vals[3][-1]}")
    print(
        f"{time_vals[-2]},{sensor_vals[0][-2]},{sensor_vals[1][-2]},{sensor_vals[2][-2]},{sensor_vals[3][-2]}\n")

    time_vals, sensor_vals = signalanalyzer.generate_squarewave(
        WAVEFORM_DURATION, use_default_vals=False, read_input=False)

    signalanalyzer.disconnect()
