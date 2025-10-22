"""Test Suite for N5 TRUMI Analysis."""


import time
import random
import datetime

from NSTA.testscripts.test_script import TestScript
from standalone_scripts.devicelogs_serialparser.n5_device_logs import SerialLogger, ConvertLogs


class TRUMI_RelocationMessageContent(TestScript):
    """Check UL Message Contents for a TRUMI Relocation Cycle.

    Purpose of this test is check UL message contents through a TRUMI relocation cycles. A shaker is to be used to simulate motion.

    Pre-conditions:
        - An activated tracker with speed threshold = 40km/h and distance threshold = 2km mounted on an IKAHS501 Lab Shaker
        - Access to AlpsAlpine API Platform
    """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_RelocationMessageContent"
        self.automation_content = "TRUMI_RelocationMessageContent"
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAHS501")
        self.n_steps = 4

    def teststeps(self):
        # Step 1: Start shaker with 150 RPM for 5 minutes
        step_description = "Start shaking at 150 RPM for 5 minutes"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info(step_description)
        self.EQUIPMENT.start_shaking(150)
        time.sleep(300)
        self.save_step(1, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 2: Stop shaking and wait 1 minute
        step_description = "Start shaking at 150 RPM for 5 minutes"
        expected_result = "Exactly 1 Status message is visible in the backend"
        actual_result = ""
        self.logger.info(step_description)
        self.EQUIPMENT.stop()
        time.sleep(60)
        self.logger.info("Check backend for messages")
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc=t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            if message_["decodedMsg"]["messageType"] not in ("NBIOT_DIAGNOSTICS", "NBIOT_BOOT",):
                # Ignore unwanted messages
                backend_messages.append(message_)
        backend_messages = list(reversed(backend_messages))     # Reverse for convenience
        if len(backend_messages) != 1:
            actual_result = f"Unexpected number of backend messages: {len(backend_messages)}"
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            actual_result = "Message found in the backend"
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 3: Check backend message content from the previous step
        step_description = "Check backend message content"
        expected_result = "Message type is ALPS_STATUS"
        actual_result = ""
        message_raw = backend_messages[0]
        try:
            message_type = message_raw["decodedMsg"]["messageType"]
        except KeyError as e_:
            message_type = "_UNKNOWN_"
        if message_type == "ALPS_STATUS":
            self.save_step(3, step_description, expected_result, f"Message Type: {message_type}", self.result_classifier.PASSED)
        else:
            self.save_step(3, step_description, expected_result, f"Message Type: {message_type}", self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return

        # Step 4: Wait additional 10 minutes and check backend
        step_description = "Check backend message content"
        expected_result = "Message type is ALPS_NORMAL_WIFI_LOCATION"
        actual_result = ""
        self.logger.info("Wait 10 + 1 minutes")
        t3 = self._get_current_ts_utc()
        time.sleep(660)
        t4 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t3, end_time_utc=t4, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            if message_["decodedMsg"]["messageType"] not in ("NBIOT_DIAGNOSTICS", "NBIOT_BOOT",):
                # Ignore unwanted messages
                backend_messages.append(message_)
        backend_messages = list(reversed(backend_messages))     # Reverse for convenience
        if len(backend_messages) != 1:
            actual_result = f"Unexpected number of backend messages: {len(backend_messages)}"
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        message_raw = backend_messages[0]
        try:
            message_type = message_raw["decodedMsg"]["messageType"]
        except KeyError as e_:
            message_type = "_UNKNOWN_"
        if message_type == "ALPS_NORMAL_WIFI_LOCATION":
            self.save_step(4, step_description, expected_result, f"Message Type: {message_type}", self.result_classifier.PASSED)
        else:
            self.save_step(4, step_description, expected_result, f"Message Type: {message_type}", self.result_classifier.FAILED)
            return

    def _get_current_ts_utc(self):
        current_timestamp_utc = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%dT%H:%M:%S")
        return current_timestamp_utc


class TRUMI_ShakeIt(TestScript):
    """Shake and analyze.

    With no particular test spec, here we are trying to undrestand device AXL
    behavior WRT various shake patterns.

    Pre-conditions:
        - An activated tracker with speed threshold = 40km/h and distance threshold = 2km mounted on an IKAHS501 Lab Shaker
        - Mounted devices on a IKA HS501 shaker with accelerometer data available via UART
    """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_ShakeIt"
        self.automation_content = "TRUMI_ShakeIt"
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):
        # Step X: Start shaker with 150 RPM for 5 minutes
        rpm_min, rpm_max = 150, 250
        rpm_step = 50
        shake_duration_min, shake_duration_max = 1, 1
        shake_duration_step = 1
        waiting_time_after_stop = 10
        
        self.EQUIPMENT =  self.EQUIPMENT[0]
        self.DUT.get_frames()

        for rpm_ in range(rpm_min, rpm_max + rpm_step, rpm_step):
            for shake_duration_ in range(shake_duration_min, shake_duration_max + shake_duration_step, shake_duration_step):
                self.logger.info(f"Start Shaking at {rpm_} RPM for {shake_duration_} seconds")
                self.EQUIPMENT.start_shaking(rpm_)
                time.sleep(shake_duration_)
                self.logger.info("Stop Shaking")
                self.EQUIPMENT.stop()
                self.logger.info(f"Wait {waiting_time_after_stop} seconds to get back to STORED")
                time.sleep(waiting_time_after_stop)
        self.save_step(1, "Shake on given parameters", "Shake on given parameters", "Shake on given parameters", self.result_classifier.PASSED)


class TRUMI_Benchmark(TestScript):
    """This testcase uses the shaker system to execute TRUMI or accel analysis

    There are two modes of operation:
        Manual:
            The logger devices need to be connected to their respective COM ports manually
            and the logging should be started before running the testcase.
        Automated:
            the data_logging_en parameter should be set in the teststation_config file and 
            the logs will be recorded automatically
    """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Benchmark"
        self.automation_content = "TRUMI_Benchmark"
        self.version = 0.1
        self.requirement["EQUIPMENT"].append("SHKR2075E")
        self.n_steps = 1

    def teststeps(self):
        # Set config parameters
        test_parameters = self.params_from_testcfg
        FREQUENCY_ARRAY = test_parameters.get('frequency')
        DURATION_ARRAY = test_parameters.get('duration')
        VOLTAGE_ARRAY = test_parameters.get('voltage')

        # Step X: Set logging time based on defined parameters
        waiting_time_after_stop = 900  # More than 10 min
        logtime = 0
        for voltage in VOLTAGE_ARRAY:
            for duration in DURATION_ARRAY:
                for frequency in FREQUENCY_ARRAY:
                    logtime += duration + waiting_time_after_stop
        self.logger.info(f"Total logtime: {logtime} seconds")

        # Step X2: Setup Equipment
        for equ in self.EQUIPMENT:
            if equ.name == "SHKR2075E":
                shaker_signal = equ

        # Step 1,2,...: Connect to shaker and send signals
        step = 1
        time.sleep(5)
        for voltage in VOLTAGE_ARRAY:
            for duration in DURATION_ARRAY:
                for frequency in FREQUENCY_ARRAY:
                    start_time = datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')
                    # file_suffix = f"_{frequency}Hz_{voltage}V_{duration}s_{timestamp}"
                    self.logger.info(f"Start Shaking at {frequency}Hz {voltage}Vpp for {duration} seconds")
                    shaker_signal.send_output_threaded(frequency, voltage, duration, delay_start=True)
                    shaker_signal.wait_for_thread_finish()
                    self.logger.info("Stop Shaking")
                    self.logger.info(f"Waiting for {waiting_time_after_stop} seconds for device to settle.")
                    time.sleep(waiting_time_after_stop)
                    end_time =  datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')
                    self.save_step(step, f"Shake at {frequency}Hz {voltage}Vpp for {duration} seconds", "Shake Started and Finished", f"Shake Started at {start_time} and Finished at {end_time}", self.result_classifier.PASSED)
                    step += 1
        self.logger.info(f"Execution Finished.")

class TRUMI_Benchmark_Random(TestScript):
    """This testcase uses the shaker system to execute TRUMI or accel analysis

    There are two modes of operation:
        Manual:
            The logger devices need to be connected to their respective COM ports manually
            and the logging should be started before running the testcase.
        Automated:
            the data_logging_en parameter should be set in the teststation_config file and 
            the logs will be recorded automatically
    """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Benchmark"
        self.automation_content = "TRUMI_Benchmark"
        self.version = 0.1
        # self.requirement["EQUIPMENT"].append("SHKR2075E")
        self.n_steps = 1

    def teststeps(self):
        # Set config parameters
        test_parameters = self.params_from_testcfg
        FREQUENCY_RANGE = test_parameters.get('frequency')
        DURATION_ARRAY = test_parameters.get('duration')
        VOLTAGE_ARRAY = test_parameters.get('voltage')
        FREQUENCY_ARRAY = []
        NO_OF_RNDM_FREQ = 5
        for _ in range(NO_OF_RNDM_FREQ):
            frequency = round(random.uniform(FREQUENCY_RANGE[0], FREQUENCY_RANGE[1]), 3)
            FREQUENCY_ARRAY.append(frequency)

        # Step X: Set logging time based on defined parameters
        waiting_time_after_stop = 900  # More than 10 min
        logtime = 0
        for voltage in VOLTAGE_ARRAY:
            for duration in DURATION_ARRAY:
                for frequency in FREQUENCY_ARRAY:
                    logtime += duration + waiting_time_after_stop
        self.logger.info(f"Total logtime: {logtime} seconds")

        # Step X2: Setup Equipment
        for equ in self.EQUIPMENT:
            if equ.name == "SHKR2075E":
                shaker_signal = equ

        # Step 1,2,...: Connect to shaker and send signals
        step = 1
        time.sleep(5)
        for voltage in VOLTAGE_ARRAY:
            for duration in DURATION_ARRAY:
                for frequency in FREQUENCY_ARRAY:
                    start_time = datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')
                    # file_suffix = f"_{frequency}Hz_{voltage}V_{duration}s_{timestamp}"
                    self.logger.info(f"Start Shaking at {frequency}Hz {voltage}Vpp for {duration} seconds")
                    shaker_signal.send_output_threaded(frequency, voltage, duration, delay_start=True)
                    shaker_signal.wait_for_thread_finish()
                    end_time =  datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')
                    self.logger.info("Stop Shaking")
                    self.logger.info(f"Waiting for {waiting_time_after_stop} seconds for device to settle.")
                    time.sleep(waiting_time_after_stop)
                    self.save_step(step, f"Shake at {frequency}Hz {voltage}Vpp for {duration} seconds", "Shake Started and Finished", f"Shake Started at {start_time} and Finished at {end_time}", self.result_classifier.PASSED)
                    step += 1
        self.logger.info(f"Execution Finished.")
        
############################################################################
### Note: the following test cases are designed for testing TRUMI v3.5.0 ###     
############################################################################             
STATE_DSLEEP = 1.0
STATE_LSLEEP = 1.5
STATE_TRUMI = 2.0
STATE_RELOC = 3.0
TRUMI_STATE_TRANSITION_TIMEOUT_s = 60
LIGHTSLEEP_STATE_TRANSITION_TIMEOUT_s = 9 * 60
DEEPSLEEP_STATE_TRANSITION_TIMEOUT_s = TRUMI_STATE_TRANSITION_TIMEOUT_s + LIGHTSLEEP_STATE_TRANSITION_TIMEOUT_s
class TRUMI_State_Transition_Base(TestScript):
    """This testcase uses the shaker system to execute TRUMI or accel analysis 
    
    This testcase is used by the following testcases to check state transitions

    There are two modes of operation:
        Manual:
            The logger devices need to be connected to their respective COM ports manually
            and the logging should be started before running the testcase.
        Automated:
            the data_logging_en parameter should be set in the teststation_config file and 
            the logs will be recorded automatically
            
    Note: the following test cases are designed for testing TRUMI v3.5.0
    """
    def __init__(self):
        super().__init__()
        self.freq_hz = None
        self.duration_s = None
        self.voltage_v = None
        # FIXED FW VARIABLES

        self.trumi_timeout = DEEPSLEEP_STATE_TRANSITION_TIMEOUT_s
        
    def set_shaker_params(self, freq, duration, voltage):
        """Set the parameters for the shaker.

        :param freq: Frequency of the shaker
        :type freq: int
        :param duration: Duration of the shaking
        :type duration: int
        :param voltage: Voltage of the shaker
        :type voltage: float
        """
        self.freq_hz = freq
        self.duration_s = duration
        self.voltage_v = voltage
        
    def run_vibration_shaker_loop(self, shaker_signal, step_no):
        """Run the vibration shaker loop.

        :param shaker_signal: The equipment object for the shaker
        :type shaker_signal: Equipment
        :param step_no: The step number of the execution
        :type step_no: int
        """
        time.sleep(5)
        start_time = datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')
        self.logger.info(f"Start Shaking at Motion Threshold for {self.duration_s} seconds")
        shaker_signal.send_output_threaded(self.freq_hz, self.voltage_v, self.duration_s, delay_start=True)
        shaker_signal.wait_for_thread_finish()
        end_time =  datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S]')
        self.logger.info("Stop Shaking")
        self.save_step(step_no, f"Shake at {self.freq_hz}Hz {self.voltage_v}Vpp for {self.duration_s} seconds", "Shake Started and Finished", f"Shake Started at {start_time} and Finished at {end_time}", self.result_classifier.PASSED)
        
    def wait_for_device_timeout(self, wait_time, step_no):
        """Wait for the device to timeout.

        :param wait_time: The time to wait for the device
        :type wait_time: int
        :param step_no: The step number of the execution
        :type step_no: int
        """
        self.logger.info(f"Waiting for {wait_time} seconds for device to settle.")
        time.sleep(wait_time)
        self.save_step(step_no, f"Wait for {wait_time} seconds", "Wait Finished", f"Wait Finished", self.result_classifier.PASSED)
    
    def parse_log_files(self):
        """Parse the log files for TRUMI state transitions.

        This function should be implemented in subclasses to parse the log files
        and extract the TRUMI state transitions.
        """
        # This function should be implemented in subclasses to parse the log files
        pass
        
    def analyze_trumi_states(self, expected_transitions, expected_durations):
        """Analyze the TRUMI states.

        :param expected_states: The expected states of the TRUMI state machine
        :type expected_states: list
        """
        # This function should be implemented in subclasses to analyze the TRUMI states
        pass


class TRUMI_State_Transition_TRUMI(TRUMI_State_Transition_Base):
    """This testcase uses the shaker system to execute TRUMI or accel analysis 
    
    This testcase triggers the TRUMI state machine to receive the following states:
    
    Expected state: [TRUMI]
    Additional States: [SLEEP or LIGHT_SLEEP → DEEP_SLEEP]
    Aim: Enters TRUMI state
    
    """
    def __init__(self):
        super().__init__()
        self.name = "TRUMI_State_Transition_TRUMI"
        self.automation_content = "TRUMI_State_Transition_TRUMI"
        self.version = 0.1
        self.requirement["EQUIPMENT"].append("SHKR2075E")
        self.n_steps = 1
        
    def teststeps(self):
        # Set config parameters (fixed values as per testcase requirement)
        test_parameters = self.params_from_testcfg
        waiting_time_after_stop = self.trumi_timeout + 300  # 5 min on top of timeout
        
        # Step X: Set logging time based on defined parameters
        logtime = waiting_time_after_stop
        self.logger.info(f"Total logtime: {logtime} seconds")

        # Step X2: Setup Equipment
        for equ in self.EQUIPMENT:
            if equ.name == "SHKR2075E":
                shaker_signal = equ
        devices = self.DUT

        # Step 1,2,...: Connect to devices, shaker and send signals
        self.set_shaker_params(50, 120, 0.1)
        self.run_vibration_shaker_loop(shaker_signal, step_no=1)
        self.wait_for_device_timeout(waiting_time_after_stop, step_no=2)
        self.logger.info(f"Execution Finished.")
        
        # Step Z: Analyze and append results
        expected_transitions = [STATE_TRUMI, STATE_LSLEEP]
        expected_durations = [TRUMI_STATE_TRANSITION_TIMEOUT_s, LIGHTSLEEP_STATE_TRANSITION_TIMEOUT_s]
        self.analyze_trumi_states(expected_transitions, expected_durations)

class TRUMI_State_Transition_RELOC(TRUMI_State_Transition_Base):
    """This testcase uses the shaker system to execute TRUMI or accel analysis 
    
    This testcase triggers the TRUMI state machine to receive the following states:
    
    Expected state: [TRUMI → RELOC]
    Additional States: [SLEEP or LIGHT_SLEEP → DEEP_SLEEP]
    Aim: Enters RELOCATION state
    
    """
    def __init__(self):
        super().__init__()
        self.name = "TRUMI_State_Transition_RELOC"
        self.automation_content = "TRUMI_State_Transition_RELOC"
        self.version = 0.1
        self.requirement["EQUIPMENT"].append("SHKR2075E")
        self.n_steps = 1
        
    def teststeps(self):
        # Set config parameters (fixed values as per testcase requirement)
        test_parameters = self.params_from_testcfg
        waiting_time_after_stop = self.trumi_timeout + 300  # 5 min on top of timeout
        
        # Step X: Set logging time based on defined parameters
        logtime = waiting_time_after_stop
        self.logger.info(f"Total logtime: {logtime} seconds")

        # Step X2: Setup Equipment
        for equ in self.EQUIPMENT:
            if equ.name == "SHKR2075E":
                shaker_signal = equ

        # Step 1,2,...: Connect to shaker and send signals
        self.set_shaker_params(10, 600, 0.2)
        self.run_vibration_shaker_loop(shaker_signal, step_no=1)
        self.wait_for_device_timeout(waiting_time_after_stop, step_no=2)
        self.logger.info(f"Execution Finished.")


class TRUMI_State_Transition_Keep_TRUMI_Variables(TRUMI_State_Transition_Base):
    """This testcase uses the shaker system to execute TRUMI or accel analysis 
    
    This testcase triggers the TRUMI state machine to receive the following states:
    
    Expected state: [TRUMI → LIGHT_SLEEP → TRUMI → RELOCATION]
    Additional States: [SLEEP or LIGHT_SLEEP → DEEP_SLEEP]
    Aim: Keeps record of TRUMI variables of SPEED and DISTANCE
    
    """
    def __init__(self):
        super().__init__()
        self.name = "TRUMI_State_Transition_Keep_TRUMI_Variables"
        self.automation_content = "TRUMI_State_Transition_Keep_TRUMI_Variables"
        self.version = 0.1
        self.requirement["EQUIPMENT"].append("SHKR2075E")
        self.n_steps = 1
        
    def teststeps(self):
        # Set config parameters (fixed values as per testcase requirement)
        test_parameters = self.params_from_testcfg
        waiting_time_after_stop = self.trumi_timeout + 300  # 5 min on top of timeout
        
        # Step X: Set logging time based on defined parameters
        logtime = waiting_time_after_stop
        self.logger.info(f"Total logtime: {logtime} seconds")

        # Step X2: Setup Equipment
        for equ in self.EQUIPMENT:
            if equ.name == "SHKR2075E":
                shaker_signal = equ

        # Step 1,2,...: Connect to shaker and send signals
        self.set_shaker_params(50, 120, 0.2)
        self.run_vibration_shaker_loop(shaker_signal, step_no=1)
        time.sleep(150)
        self.set_shaker_params(10, 600, 0.2)
        self.run_vibration_shaker_loop(shaker_signal, step_no=2)
        self.wait_for_device_timeout(waiting_time_after_stop, step_no=3)
        self.logger.info(f"Execution Finished.")
        
        
class TRUMI_State_Transition_Clear_TRUMI_Variables(TRUMI_State_Transition_Base):
    """This testcase uses the shaker system to execute TRUMI or accel analysis 
    
    This testcase triggers the TRUMI state machine to receive the following states:
    
    Expected state: [TRUMI → LIGHT_SLEEP → DEEP_SLEEP → TRUMI → RELOCATION]
    Additional States: [SLEEP or LIGHT_SLEEP → DEEP_SLEEP]
    Aim: Clears record of TRUMI variables of SPEED and DISTANCE
    
    """
    def __init__(self):
        super().__init__()
        self.name = "TRUMI_State_Transition_Clear_TRUMI_Variables"
        self.automation_content = "TRUMI_State_Transition_Clear_TRUMI_Variables"
        self.version = 0.1
        self.requirement["EQUIPMENT"].append("SHKR2075E")
        self.n_steps = 1
        
    def teststeps(self):
        # Set config parameters (fixed values as per testcase requirement)
        test_parameters = self.params_from_testcfg
        waiting_time_after_stop = self.trumi_timeout + 300  # 5 min on top of timeout
        
        # Step X: Set logging time based on defined parameters
        logtime = waiting_time_after_stop
        self.logger.info(f"Total logtime: {logtime} seconds")

        # Step X2: Setup Equipment
        for equ in self.EQUIPMENT:
            if equ.name == "SHKR2075E":
                shaker_signal = equ

        # Step 1,2,...: Connect to shaker and send signals
        self.set_shaker_params(50, 120, 0.1)
        self.run_vibration_shaker_loop(shaker_signal, step_no=1)
        self.wait_for_device_timeout(waiting_time_after_stop, step_no=2)
        self.set_shaker_params(10, 600, 0.2)
        self.run_vibration_shaker_loop(shaker_signal, step_no=1)
        self.wait_for_device_timeout(waiting_time_after_stop, step_no=2)
        self.logger.info(f"Execution Finished.")


# UNDER CONSTRUCTION
# class TRUMI_VibrationRun(TestScript):
#     def __init__(self):
#         super().__init__()
#         self.name = "TRUMI_Analysis"
#         self.automation_content = "TRUMI_Analysis"
#         self.version = 0.1
#         # self.requirement["DUT"].append("PlatformDevice")
#         self.requirement["EQUIPMENT"].append("SHKR2075E")
#         self.requirement["EQUIPMENT"].append("DT9837")
#         self.n_steps = 1

#     def teststeps(self):
#         # Step X: Start shaker at 5Hz with 0.1 Vpp for 10 seconds
#         frequency = 5
#         voltage = 0.1
#         duration = 10
#         operation = 'THREADED'

#         shaker_signal = self.EQUIPMENT[0]
#         signal_analyzer = self.EQUIPMENT[1]
#         # FOR MANUAL OPERATION
#         # the following functions will be used:
#         #   shaker_signal.enable_output()
#         #   shaker_signal.send_output_manual(frequency, voltage)
#         #   time.sleep(5) # or measurement function delay
#         #   shaker_signal.disable_output()

#         # FOR THREADED OPERATION
#         # the following functions will be used:
#         #   shaker_signal.send_output_threaded(frequency, voltage, duration, delay_start=True)
#         #   time.sleep(5) # or measurement function delay
#         #   shaker_signal.wait_for_thread_finish()
#         shaker_signal.connect()
#         signal_analyzer.connect()
#         self.logger.info(f"Start Shaking at {voltage} V for {duration} seconds")
#         if operation == 'MANUAL':
#             shaker_signal.enable_output()
#             shaker_signal.send_output_manual(frequency, voltage)
#             time_vals, sensor_vals = signal_analyzer.measure_acceleration(duration)
#             shaker_signal.disable_output()
#         elif operation == 'THREADED':
#             shaker_signal.send_output_threaded(frequency, voltage, duration, delay_start=True)
#             time_vals, sensor_vals = signal_analyzer.measure_acceleration(duration)
#             shaker_signal.wait_for_thread_finish()
#         self.logger.info("Stop Shaking")
#         time.sleep(1)
#         signal_analyzer.save_measurement_to_csv(time_vals, sensor_vals)
#         shaker_signal.disconnect()
#         signal_analyzer.disconnect()
#         self.save_step(1, "Shake on given parameters", "Shake on given parameters", "Shake on given parameters", self.result_classifier.PASSED)

# UNDER CONSTRUCTION
# class TRUMI_VibrationLoop(TestScript):
#     def __init__(self):
#         super().__init__()
#         self.name = "TRUMI_Analysis"
#         self.automation_content = "TRUMI_Analysis"
#         self.version = 0.1
#         # self.requirement["DUT"].append("PlatformDevice")
#         self.requirement["EQUIPMENT"].append("SHKR2075E")
#         self.requirement["EQUIPMENT"].append("DT9837")
#         self.n_steps = 1

#     def teststeps(self):
#         # Step X: Start shaker at 5Hz with 0.1 Vpp for 10 seconds
#         frequency = 5
#         voltage = 0.1
#         duration = 60
#         waiting_time_after_stop = 900
#         timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#         file_suffix = f"_{frequency}Hz_{voltage}V_{duration}s_{timestamp}"
#         filename = "standalone_scripts/devicelogs_serialparser/TEMP_DEV_LOGS/"

#         # TODO: Add frequency loop
#         shaker_signal = self.EQUIPMENT[0]
#         signal_analyzer = self.EQUIPMENT[1]
#         device_logger = SerialLogger()
#         shaker_signal.connect()
#         signal_analyzer.connect()

#         self.logger.info(f"Start Shaking at {voltage} V for {duration} seconds")
#         device_logger.start_serial_thread(duration)
#         shaker_signal.send_output_threaded(frequency, voltage, duration, delay_start=True)
#         time_vals, sensor_vals = signal_analyzer.measure_acceleration(duration)
#         shaker_signal.wait_for_thread_finish()
#         device_logger.wait_for_serial_thread()
#         self.logger.info("Stop Shaking")
#         time.sleep(1)
#         signal_analyzer.save_measurement_to_csv(time_vals, sensor_vals, filename=filename, suffix=file_suffix)
#         device_logger.parse_measurement(filename=filename, suffix=file_suffix)
#         shaker_signal.disconnect()
#         signal_analyzer.disconnect()

# UNDER CONSTRUCTION
# class TRUMI_Benchmark_Automated(TestScript):
#     def __init__(self):
#         super().__init__()
#         self.name = "TRUMI_Analysis"
#         self.automation_content = "TRUMI_Analysis"
#         self.version = 0.1
#         self.requirement["DUT"].append("N5")
#         self.requirement["DUT"].append("L5")
#         self.requirement["EQUIPMENT"].append("SHKR2075E")
#         self.n_steps = 1

#     def teststeps(self):
#         # Set config parameters
#         test_parameters = self.params_from_testcfg
#         FREQUENCY_ARRAY = test_parameters.get('frequency')
#         DURATION_ARRAY = test_parameters.get('duration')
#         VOLTAGE_ARRAY = test_parameters.get('voltage')

#         # Step X: Set logging time based on defined parameters
#         waiting_time_after_stop = 900  # More than 10 min
#         logtime = 0
#         for voltage in VOLTAGE_ARRAY:
#             for duration in DURATION_ARRAY:
#                 for frequency in FREQUENCY_ARRAY:
#                     logtime += duration + waiting_time_after_stop
#         self.logger.info(f"Total logtime: {logtime} seconds")
#         timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
#         filename = "standalone_scripts/devicelogs_serialparser/TEMP_DEV_LOGS/"
#         file_suffix = f"_{timestamp}"

#         # TODO: add logger to framework and initialize at connect()
#         # Step X2: Setup logging
#         devices = []
#         for device in self.DUT:
#             devices.append(SerialLogger(port=device.port,dev_name=device.name))
#         for device in devices:
#             device.start_serial_thread(logtime)

#         for equ in self.EQUIPMENT:
#             if equ.name == "SHKR2075E":
#                 shaker_signal = equ

#         # Step 1,2,...: Connect to shaker and send signals
#         time.sleep(5)
#         for voltage in VOLTAGE_ARRAY:
#             for duration in DURATION_ARRAY:
#                 for frequency in FREQUENCY_ARRAY:
#                     # file_suffix = f"_{frequency}Hz_{voltage}V_{duration}s_{timestamp}"
#                     self.logger.info(f"Start Shaking at {frequency}Hz {voltage}Vpp for {duration} seconds")
#                     shaker_signal.send_output_threaded(frequency, voltage, duration, delay_start=True)
#                     shaker_signal.wait_for_thread_finish()
#                     self.logger.info("Stop Shaking")
#                     self.logger.info(f"Waiting for {waiting_time_after_stop} seconds for device to settle.")
#                     time.sleep(waiting_time_after_stop)
#         for device in devices:
#             device.wait_for_serial_thread()

#         # Step X3: parse logs to readable format
#         time.sleep(1)
#         for device in devices:
#             device.parse_measurement(filename=filename, suffix=file_suffix)


if __name__ == "__main__":
    pass
