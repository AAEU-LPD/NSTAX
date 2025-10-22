"""Test Suite for Miscellaneous Utility Workflows."""


import os
import pandas as pd

from NSTA.testscripts.test_script import TestScript


class PlatformDeviceMessageLoggerCSV(TestScript):
    """Generate CSV of platform messages. Not really a test case, rather a auto log creator for convenience.

    With a give time range, this testcase generates a CSV containing timestamp and temperature data from following messages:
        1. N5: ALPS_STATUS -> STATUS_FUNCTION_SPECIFIC -> TEMPERATURE
        2. HATI: SENSOR_DATA -> temperature
    """
    def __init__(self):
        super().__init__()
        self.name = "PlatformDeviceMessageLoggerCSV"
        self.automation_content = "PlatformDeviceMessageLoggerCSV"
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 3
        # Testcase specifics
        self.start_time_utc = "2023-08-07T15:15:59"
        self.end_time_utc = "2023-08-08T15:15:59"

    def initialize(self):
        super().initialize()
        # self.csv_path = os.path.join(self.log_folder, f"temperature_log_{os.path.basename(self.log_folder)}.csv")

    def teststeps(self):
        """Test steps."""
        # Step 0: Get test parameters
        
        test_parameters = self.params_from_testcfg
        start_time_utc = test_parameters.get("start_time_utc")
        end_time_utc = test_parameters.get("end_time_utc")
        max_message_count = test_parameters.get("max_message_count")
        self.csv_path = os.path.join(self.log_folder, f"{self.DUT.name}_temperature_log_{os.path.basename(self.log_folder)}.csv")   ### take up??

        # Step 1: Read from backend
        # start_time_utc = "2023-08-07T15:15:59"
        # end_time_utc = "2023-08-08T15:15:59"
        backend_messages = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_messages=max_message_count)
        backend_messages = list(reversed(backend_messages))     # Reverse for convenience
        info_text = f"Get messages between {start_time_utc} and {end_time_utc} (UTC)"
        self.logger.info(info_text)
        self.save_step(1, info_text, info_text, info_text, self.result_classifier.PASSED)

        # Step 2: Organize data
        timestamp_list = []
        temperature_list = []
        for message_raw in backend_messages:
            # Get message type
            try:
                message_type = message_raw["decodedMsg"]["messageType"]
            except KeyError as e_:
                message_type = "_UNKNOWN_"
            if message_type == "SENSOR_DATA":
                # HATI
                try:
                    sensor_data = message_raw["decodedMsg"]["sensorDataValues"]
                    message_generation_time = message_raw["decodedMsg"]["messageDate"]
                except KeyError as e_:
                    sensor_data = {}
                    message_generation_time = "-"
                if sensor_data.get("SENSOR_TYPE") == "temperature":
                    temperature_readout = sensor_data.get("MEASUREMENT_0", "-")
                else:
                    continue    # continue since wrong sensor type
            elif message_type == "ALPS_STATUS":
                # N5
                try:
                    alps_message_type = message_raw["decodedMsg"]["payload"]["alpsMessageType"]
                    specific_function = message_raw["decodedMsg"]["payload"]["functionHeader"]["function"]
                except KeyError as e_:
                    alps_message_type = specific_function = None
                if alps_message_type == "STATUS_FUNCTION_SPECIFIC" and specific_function == "TEMPERATURE":
                    try:
                        temperature_readout = message_raw["decodedMsg"]["payload"]["temperature"]["temperature"]
                        message_generation_time = message_raw["decodedMsg"]["header"]["messageGenerationTime"]
                    except KeyError as e_:
                        temperature_readout = message_generation_time = "-"
                else:
                    continue    # continue since wrong function specific message type
            else:
                continue

            timestamp_list.append(message_generation_time)
            temperature_list.append(temperature_readout)
            info_text = "Organize data"
        self.save_step(2, info_text, info_text, info_text, self.result_classifier.PASSED)

        # Step 3: Write CSV
        pd_dict = {"Timestamp": timestamp_list, "Temperature": temperature_list}
        pd_dataframe = pd.DataFrame(pd_dict)
        pd_dataframe.to_csv(self.csv_path, encoding="utf-8", index=False)
        info_text = f"Save to {self.csv_path}"
        self.save_step(3, info_text, info_text, info_text, self.result_classifier.PASSED)


if __name__ == "__main__":
    pass
