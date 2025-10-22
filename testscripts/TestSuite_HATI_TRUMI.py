"""Test Suite for HATI TRUMI Analysis"""


from NSTAX.testscripts.test_script import TestScript
import time
from pprint import pprint
import datetime
from itertools import combinations


class BaseTestUtils(TestScript):
    """Detect and Track HATI device in a Drive Test (TRUMI).

    Here, This tests the following testsuites:  

    Testsuite:
        - Status Relocation Start Message
        - Status On The Move Single Message
        - Status On The Move Multiple Messages
        - Relocation Start Message Timings
        - Status Destination Reached Message

    Prerequisite: 
        Configure DUT profile configuration as follows: 
        for example: 
        - Are locations captured while moving?: Every 3 minutes;
        - When is a stop detected?: 10 minutes without movement
    """

    def __init__(self):
        super().__init__()

    def _get_interface_time_range(self, moving_time_sec: int, waiting_time_sec: int):
        """Return: start_time, end_time"""

        current_time_utc = datetime.datetime.utcnow()

        # a_min_befr_curr_time_delta = datetime.timedelta(minutes=1)

        a_min_befr_curr_time_delta = datetime.timedelta(minutes=0)
        start_time_utc = current_time_utc - a_min_befr_curr_time_delta

        # total_waiting_utc = datetime.timedelta(
        #     seconds=moving_time_sec + waiting_time_sec + 120)

        total_waiting_utc = datetime.timedelta(
            seconds=moving_time_sec + waiting_time_sec)

        end_time_utc = start_time_utc + total_waiting_utc

        start_time_str = start_time_utc.strftime("%Y-%m-%dT%H:%M:%S")
        end_time_str = end_time_utc.strftime("%Y-%m-%dT%H:%M:%S")

        return start_time_str, end_time_str

    def _calculate_time_difference(self, start_time_utc: str, end_time_utc: str):
        """Calculate the difference between two dates

        args: 
            - start_time_utc: A time stamp
            - end_time_utc: A time stamp 

        Returns:
            - mins: int
        """
        time_format = "%Y-%m-%dT%H:%M:%S%z"

        # Add +0000 if it's not already there, to match the sensolus backend.
        if '+' not in start_time_utc and '-' not in start_time_utc[-6:]:
            start_time_utc += "+0000"
        if '+' not in end_time_utc and '-' not in end_time_utc[-6:]:
            end_time_utc += "+0000"

        start_time = datetime.datetime.strptime(start_time_utc, time_format)
        end_time = datetime.datetime.strptime(end_time_utc, time_format)

        time_diff = end_time - start_time

        minutes = time_diff.total_seconds() / 60

        return minutes

    def _search_messages_for_device_location_start(self, data_list: list):
        """Search the retrieved data from sensolus backend, for a start, location update

        args: 
            - data_list: An array of the messages from sensolus backend 

        Returns:
            - tuple: boolean, found_object
        """

        for message in data_list:
            for data in message["data"]:
                message_type = data["decodedMsg"].get("messageType")
                message_state = data["decodedMsg"].get("state")
                if message_type == "LOCATION_UPDATE" or message_state == "START":
                    return True, data["decodedMsg"]
        else:
            return False, None

    def _search_messages_for_device_on_move(self, data_list: list):
        """Search the retrieved data from sensolus backend, for an 'on_move', location update

        args: 
            - data_list: An array of the messages from sensolus backend 

        Returns:
            - tuple: boolean, array of objects
        """
        on_the_move_data_list = []

        for message in data_list:
            for data in message["data"]:
                message_type = data["decodedMsg"].get("messageType")
                message_state = data["decodedMsg"].get("state")
                if message_state == "ON_THE_MOVE":
                    on_the_move_data_list.append(data["decodedMsg"])

        return (
            True if on_the_move_data_list else False,
            on_the_move_data_list
        )

    def _search_messages_for_device_journey_end(self, data_list: list):
        """Search the retrieved data from sensolus backend, for an 'STOP'

        args: 
            - data_list: An array of the messages from sensolus backend 

        Returns:
            - tuple: boolean, array of objects
        """
        stop_data_list = []

        for message in data_list:
            for data in message["data"]:
                message_type = data["decodedMsg"].get("messageType")
                message_state = data["decodedMsg"].get("state")
                message_event = data["decodedMsg"].get("event")
                if message_state == "STOP" or message_event == "STOP":
                    stop_data_list.append(data["decodedMsg"])

        return (
            True if stop_data_list else False,
            stop_data_list
        )

    def shake_equipment(self, equipment: object, rpm: int, duration: int, wait_time: int):
        """Shake an equipment"""

        self.logger.info(f"Shaking at {rpm} RPM for {duration} secs ...")
        equipment.start_shaking(rpm)

        time.sleep(duration)

        equipment.stop()
        self.logger.info(f"Stop Shaking, and waiting for {wait_time} secs ...")

        time.sleep(wait_time)

    def initiate_motion_and_get_time_frames_for_the_duration(self, step_index: int,  moving_speed_rpm: int, moving_time_sec: int, waiting_time_sec: int, no_of_dut: int = 1):
        """Initate motion shaker and get the time frame for the duration moved

        args:
            - step_index
            - moving_speed_rpm
            - moving_time_sec
            - waiting_time_sec
            - no_of_dut : specify how many device is placed on the shaker
        Return:
            - array of timeframe from backend from the distance duration. 
        """

        start_time, end_time = self._get_interface_time_range(
            moving_time_sec, waiting_time_sec)

        for equipment in self.EQUIPMENT:
            if equipment.name == "IKAKS130":

                self.shake_equipment(
                    equipment=equipment,
                    rpm=moving_speed_rpm,
                    duration=moving_time_sec,
                    wait_time=waiting_time_sec
                )
                self.save_step(
                    step_index=step_index,
                    step_description=f"Shake Device. Motion, relocation and stop journey movement",
                    expected_result=f"The equipment shaker should shake",
                    actual_result=f"The equipment shaker shooked the device for {moving_time_sec} secs, and stopped for {waiting_time_sec} secs",
                    verdict=self.result_classifier.PASSED
                )

        # ---> Step 2: Check platform backend

        self.logger.info(
            f"Retreiving the DUT time-frame, from: {start_time} - to: {end_time}")

        if no_of_dut == 1:
            time_frames = self.DUT.get_frames(
                start_time_utc=start_time, end_time_utc=end_time, max_n_frames=100)
        else:
            time_frames = [
                dut.get_frames(
                    start_time_utc=start_time, end_time_utc=end_time, max_n_frames=100)
                for dut in self.DUT
            ]
        return time_frames


class TRUMI_Status_Relocation_Start_Message_Detection(BaseTestUtils):
    """Status Relocation Start Message
        (Detect and validate when the device starts moving.)

        Test Procedure:
            - Configure the DUT device to match the requirements
            - Start shake/Move device - Drive Motion
            - Verify from the backend for a LOCATION_UPDATE and START
    """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Status_Relocation_Start_Message_Detection"
        self.automation_content = "TRUMI_Status_Relocation_Start_Message_Detection"
        self.description = "Tests detection of the initial relocation start message."
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        moving_speed_rpm = test_parameters.get("moving_speed_rpm")
        moving_time_sec = test_parameters.get("moving_time_sec")
        waiting_time_sec = test_parameters.get("waiting_time_sec")

        # ---> Step 1: Initiate Motion
        time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
            step_index=1,
            moving_speed_rpm=moving_speed_rpm,
            moving_time_sec=moving_time_sec,
            waiting_time_sec=waiting_time_sec
        )

        # ---> Step 2: Check platform backend
        if not time_frames:
            self.logger.info(
                "No messages of events found for the duration specified")
            self.save_step(
                step_index=2,
                step_description="Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="No messages of events found for the duration specified",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Messages retrieved for the movement duration.")
            self.save_step(
                step_index=2,
                step_description="Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="Messages retrieved for the movement duration.",
                verdict=self.result_classifier.PASSED
            )

        is_device_location_start_found, start_frame_data = self._search_messages_for_device_location_start(
            time_frames)

        if not is_device_location_start_found:
            self.logger.info("Device location update not found.")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started.",
                expected_result="Device location update should indicate: START",
                actual_result="Device location update not found.",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Device location update indicated: START")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started",
                expected_result="Device location update should indicate: START ",
                actual_result="Device location update indicated: START",
                verdict=self.result_classifier.PASSED
            )

        self.logger.info(
            f"Test completed: Detect device relocation start event.")


class TRUMI_Status_Single_On_the_Move_Detection(BaseTestUtils):
    """Status On The Move Single Message
        Detect and validate when the device is on the move 

        Test Procedure:
            - Configure the DUT device to match the requirements 
            - Start shake/Move device for the duration as configured - Drive Motion
            - Verify from the backend for a LOCATION_UPDATE and START (T1) event
            - Verify from the backend for a ON_THE_MOVE (T2) event
            - Compare the timestamps and calculate interval T2-T1
    """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Status_Single_On_the_Move_Detection"
        self.automation_content = "TRUMI_Status_Single_On_the_Move_Detection"
        self.description = "Tests detection of a single movement message."
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        moving_speed_rpm = test_parameters.get("moving_speed_rpm")
        moving_time_sec = test_parameters.get("moving_time_sec")
        waiting_time_sec = test_parameters.get("waiting_time_sec")

        # For the above paramters, configure the ' locations captured while moving = 3mins'

       # ---> Step 1: Initiate Motion
        time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
            step_index=1,
            moving_speed_rpm=moving_speed_rpm,
            moving_time_sec=moving_time_sec,
            waiting_time_sec=waiting_time_sec
        )

        # ---> Step 2: Check platform backend
        if not time_frames:
            self.logger.info(
                "No messages of events found for the duration specified")
            self.save_step(
                step_index=2,
                step_description="Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="No messages of events found for the duration specified",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Messages retrieved for the movement duration.")
            self.save_step(
                step_index=2,
                step_description="Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="Messages retrieved for the movement duration.",
                verdict=self.result_classifier.PASSED
            )

        # ---> 2.1
        self.logger.info(f"Searching Retrieved messages for the events")
        is_device_location_start_found, start_frame_data = self._search_messages_for_device_location_start(
            time_frames)

        if not is_device_location_start_found:
            self.logger.info("Device location update not found.")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started",
                expected_result="Device location update should indicate: START",
                actual_result="Device location update not found.",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Device location update indicated: START")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started",
                expected_result="Device location update should indicate: START ",
                actual_result="Device location update indicated: START",
                verdict=self.result_classifier.PASSED
            )

        # ---> 2.2
        is_device_on_move_found, on_move_frame_data_list = self._search_messages_for_device_on_move(
            time_frames)

        if not is_device_on_move_found:
            self.logger.info("Couldn't not detect any ON_THE_MOVE data")
            self.save_step(
                step_index=4,
                step_description="Validate device journey. (ON_THE_MOVE)",
                expected_result="Device ON_THE_MOVE with Mac Addresses",
                actual_result="Couldn't not detect any ON_THE_MOVE data",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Device ON_THE_MOVE with Mac Addresses found")
            self.save_step(
                step_index=4,
                step_description="Validate device journey. (ON_THE_MOVE)",
                expected_result="Device ON_THE_MOVE with Mac Addresses",
                actual_result="Device ON_THE_MOVE with Mac Addresses found",
                verdict=self.result_classifier.PASSED
            )

        # ---> 3: Compare the time difference (t2, t1)
        self.logger.info(
            f"Search events found within the time-frame for Device start location and 'on_the_move'. Comparing the time difference now")

        if not start_frame_data or not on_move_frame_data_list:
            self.logger.info(
                "No messages was found for device start or device on the move")
            self.save_step(
                step_index=4,
                step_description=f"Validate the time difference from the backend, if it corresponds with the time taken to trigger the first 'on_the_move' event",
                expected_result=f"The first 'on_the_move' event should be triggered within the time duration configured on the device",
                actual_result=f"No messages was found for device start or device on the move",
                verdict=self.result_classifier.FAILED
            )
        else:
            on_move_frame_data = on_move_frame_data_list[0]

            t1 = start_frame_data['messageDate']
            t2 = on_move_frame_data['messageDate']

            time_difference = self._calculate_time_difference(t1, t2)

            self.save_step(
                step_index=4,
                step_description=f"Validate the time difference from the backend, if it corresponds with the time taken to trigger the first 'on_the_move' event",
                expected_result=f"The first 'on_the_move' event should be triggered within the time duration configured on the device",
                actual_result=f"The first 'on_the_move' event was triggered within {time_difference} mins",
                verdict=self.result_classifier.PASSED
            )

        self.logger.info(
            f"Test completed: Detect device single 'on_move' event")


class TRUMI_Status_Multiple_On_the_Move_Detection(BaseTestUtils):
    """Status On The Move Multiple Messages
        Detect and validate multiple 'on the move' updates sent by the device

        Test Procedure:
            - Configure the DUT device to match the requirements
            - Start shake/Move device for the duration as configured - Drive Motion
            - Stop movement
            - Verify all on the move message generation timestamps as T1, T2, ... TN from messageDate
            - Compare the timestamps and calculate interval T2-T1
            - Check the differences between consecutive OTM message timestamps
        """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Status_Multiple_On_the_Move_Detection"
        self.automation_content = "TRUMI_Status_Multiple_On_the_Move_Detection"
        self.description = "Tests detection of multiple sequential movement messages."
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        moving_speed_rpm = test_parameters.get("moving_speed_rpm")
        moving_time_sec = test_parameters.get("moving_time_sec")
        waiting_time_sec = test_parameters.get("waiting_time_sec")

        # ---> Step 1: Initiate Motion
        time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
            step_index=1,
            moving_speed_rpm=moving_speed_rpm,
            moving_time_sec=moving_time_sec,
            waiting_time_sec=waiting_time_sec
        )

        # ---> Step 2: Check platform backend
        if not time_frames:
            self.logger.info(
                "No messages of events found for the duration specified")
            self.save_step(
                step_index=2,
                step_description="Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="No messages of events found for the duration specified",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Messages retrieved for the movement duration.")
            self.save_step(
                step_index=2,
                step_description="Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="Messages retrieved for the movement duration.",
                verdict=self.result_classifier.PASSED
            )

        # ---> 2.1
        self.logger.info(f"Searching Retrieved messages for the events")
        is_device_location_start_found, start_frame_data = self._search_messages_for_device_location_start(
            time_frames)

        if not is_device_location_start_found:
            self.logger.info("Device location update not found.")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started",
                expected_result="Device location update should indicate: START",
                actual_result="Device location update not found.",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Device location update indicated: START")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started",
                expected_result="Device location update should indicate: START ",
                actual_result="Device location update indicated: START",
                verdict=self.result_classifier.PASSED
            )

        # ---> 2.2
        is_device_on_move_found, on_move_frame_data_list = self._search_messages_for_device_on_move(
            time_frames)

        if not is_device_on_move_found:
            self.logger.info("Couldn't not detect any ON_THE_MOVE data")
            self.save_step(
                step_index=4,
                step_description="Validate device journey. (ON_THE_MOVE)",
                expected_result="Device ON_THE_MOVE with Mac Addresses",
                actual_result="Couldn't not detect any ON_THE_MOVE data",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Device ON_THE_MOVE with Mac Addresses found")
            self.save_step(
                step_index=4,
                step_description="Validate device journey. (ON_THE_MOVE)",
                expected_result="Device ON_THE_MOVE with Mac Addresses",
                actual_result="Device ON_THE_MOVE with Mac Addresses found",
                verdict=self.result_classifier.PASSED
            )

        # ---> 3: Compare the time difference between different on the move timestamps (t0, t1, t2 ... tn)
        self.logger.info(
            f"Search events found within the time-frame for Device start location and 'on_the_move'. Comparing the time difference now")

        if not on_move_frame_data_list:
            self.logger.info(
                "No messages was found for device start or device on the move")
            self.save_step(
                step_index=5,
                step_description=f"Validate the time difference from the backend, if it corresponds with the time taken to trigger the first 'on_the_move' event",
                expected_result=f"The first 'on_the_move' event should be triggered within the time duration configured on the device",
                actual_result=f"No messages was found for device start or device on the move",
                verdict=self.result_classifier.FAILED
            )
        else:
            intervals = []

            if len(on_move_frame_data_list) >= 2:
                for current, next_item in combinations(on_move_frame_data_list, 2):
                    t1 = current['messageDate']
                    t2 = next_item['messageDate']

                    time_difference = self._calculate_time_difference(t1, t2)
                    intervals.append(time_difference)
            else:
                intervals.append(0)

            text = ', '.join([f"t{i}= {interval} mins" for i,
                              interval in enumerate(intervals)])

            self.save_step(
                step_index=5,
                step_description=f"Comparing the time difference between timestamps (t0, t1, t2 ... tn)",
                expected_result=f"The time difference should tally with the interval configured on the device",
                actual_result=f"Time interval between the on_the_move events:  {text}",
                verdict=self.result_classifier.PASSED
            )

        self.logger.info(
            f"Test completed: Detect device multiple 'on_move' events")


class TRUMI_Relocation_Start_Message_Timing_Detection(BaseTestUtils):
    """Relocation Start Message Timings
        Detect and validate starts messages of the device when it moves after different stops.   

        Procedure:
            - Configure the DUT device to match the configuration 
            - Start shake/Move device for the duration as configured - Drive Motion
            - Verify LOCATION_UPDATE starting time as T1
            - Stop movement for 5 minutes 
            - Start movement again,  Note down messageDate from the LOCATION_UPDATE message as T2
            - Compare T1 and T2
            - Stop for 10+ minutes for relocation cycle to finish (STOP event is generated (state=STOP))
            - Verify journey start time
        """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Relocation_Start_Message_Timing_Detection"
        self.automation_content = "TRUMI_Relocation_Start_Message_Timing_Detection"
        self.description = "Tests detection and comparison of various journey start messages."
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):
        # ---> Step 1: Initiate Motion - 1st
        test_parameters = self.params_from_testcfg
        moving_speed_rpm = test_parameters.get("moving_speed_rpm")
        moving_time_sec = test_parameters.get("moving_time_sec")
        waiting_time_sec = test_parameters.get("waiting_time_sec")

        time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
            step_index=1,
            moving_speed_rpm=moving_speed_rpm,
            moving_time_sec=moving_time_sec,
            waiting_time_sec=waiting_time_sec
        )

        # ---> Step 2: Check platform backend
        if not time_frames:
            self.logger.info(
                "No messages of events found for the first journey duration specified")
            self.save_step(
                step_index=2,
                step_description="First journey. Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="No messages of events found for the duration specified",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info(
                "Messages retrieved for the first journey movement duration.")
            self.save_step(
                step_index=2,
                step_description="First journey. Validate if messages & events were retrieved from backend",
                expected_result="Messages retrieved for the movement duration.",
                actual_result="Messages retrieved for the movement duration.",
                verdict=self.result_classifier.PASSED
            )

        is_device_location_start_found, t1_start_frame_data = self._search_messages_for_device_location_start(
            time_frames)

        if not is_device_location_start_found:
            self.logger.info(
                "Device location update not found. First Journey (T1)")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started. First Journey (T1).",
                expected_result="Device location update should indicate: START(T1)",
                actual_result="Device location update not found. First Journey (T1)",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info(
                "Device location update found. First Journey (T1)")
            self.save_step(
                step_index=3,
                step_description="Check if the device location update was started. First Journey (T1).",
                expected_result="Device location update should indicate: START(T1)",
                actual_result="Device location update found. First Journey (T1)",
                verdict=self.result_classifier.PASSED
            )

        # ---> Step 3: Initiate Motion - 2nd

        time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
            step_index=3,
            moving_speed_rpm=moving_speed_rpm,
            moving_time_sec=moving_time_sec,
            waiting_time_sec=waiting_time_sec
        )

        # ---> Step 4: Check platform backend
        if not time_frames:
            self.logger.info("No messages was retrieved from the backend")
            self.save_step(
                step_index=4,
                step_description="Validate location update and device start state",
                expected_result="Device location update should indicate: START",
                actual_result="No messages was retrieved from the backend",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info("Messages was retrieved from the backend")
            self.save_step(
                step_index=4,
                step_description="Validate location update and device start state",
                expected_result="Device location update should indicate: START",
                actual_result="Messages was retrieved from the backend",
                verdict=self.result_classifier.PASSED
            )

        is_device_location_start_found, t2_start_frame_data = self._search_messages_for_device_location_start(
            time_frames)

        if not is_device_location_start_found:
            self.logger.info("Device location update not found. (T2)")
            self.save_step(
                step_index=5,
                step_description="Check if the device location update was started. Second Journey (T2).",
                expected_result="Device location update should indicate: START(T2)",
                actual_result="Device location update not found. (T2)",
                verdict=self.result_classifier.FAILED
            )
        else:
            self.logger.info(
                "Device location update found. Second Journey (T2).")
            self.save_step(
                step_index=5,
                step_description="Check if the device location update was started. Second Journey (T2).",
                expected_result="Device location update should indicate: START(T2)",
                actual_result="Device location update found. Second Journey (T2).",
                verdict=self.result_classifier.PASSED
            )

        self.logger.info(
            f"Test completed: Detect different journey start messages.")


class TRUMI_Status_Destination_Reached_Message_Detection(BaseTestUtils):
    """Status Destination Reached Message
        Detect and validate end-message of the device when it stops

        Procedure:
            - Configure DUT stop-detection to 10mins
            - Drive and stop for 9mins. (Expected: No stop message)
            - Drive and stop for 11mins. (Expected: Stop Message)
            - repeat the steps 1 - 2, N times
            - Verify journey end times,  journey end time must match the timestamp of the state=STOP message
        """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Status_Destination_Reached_Message_Detection"
        self.automation_content = "TRUMI_Status_Destination_Reached_Message_Detection"
        self.description = "Tests detection and comparison of various journey end messages."
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        moving_speed_rpm = test_parameters.get("moving_speed_rpm")
        moving_time_sec = test_parameters.get("moving_time_sec")
        journey1_waiting_time_sec = test_parameters.get(
            "journey1_waiting_time_sec")
        journey2_waiting_time_sec = test_parameters.get(
            "journey2_waiting_time_sec")

        # ---> Step 1: Initiate Motion & Journeys

        for idx, waiting_time_sec in enumerate([journey1_waiting_time_sec, journey2_waiting_time_sec], start=1):

            time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
                step_index=1,
                moving_speed_rpm=moving_speed_rpm,
                moving_time_sec=moving_time_sec,
                waiting_time_sec=waiting_time_sec
            )

            # ---> Step 2: Check platform messages, search for end_messages during the journey location
            journey_type = "First Journey" if idx == 1 else "Second Journey"
            # if journey is t1, no end_message expected.
            # if journey is t2, end_message is expected.

            if not time_frames:
                self.logger.info(
                    f"{journey_type}. No messages of events found for the duration specified")
                self.save_step(
                    step_index=2,
                    step_description=f"{journey_type}. Validate if messages & events were retrieved from backend",
                    expected_result=f"Messages retrieved for the movement duration.",
                    actual_result=f"No messages of events found for the duration specified",
                    verdict=self.result_classifier.FAILED
                )
            else:
                self.logger.info(
                    f"{journey_type}. Messages retrieved for the movement duration.")
                self.save_step(
                    step_index=2,
                    step_description=f"{journey_type}. Validate if messages & events were retrieved from backend",
                    expected_result=f"Messages retrieved for the movement duration.",
                    actual_result=f"Messages retrieved for the movement duration.",
                    verdict=self.result_classifier.PASSED
                )

            is_device_journey_end_found, end_frame_data = self._search_messages_for_device_journey_end(
                time_frames)

            # First Journey
            if idx == 1:
                self.save_step(
                    step_index=3,
                    step_description=f"Validate the first Journey, (T1), There should not be any STOP message",
                    expected_result=f"NO STOP message found",
                    actual_result=f"NO STOP message found" if not is_device_journey_end_found else "STOP message found",
                    verdict=self.result_classifier.PASSED if not is_device_journey_end_found else self.result_classifier.FAILED
                )

            # Second Journey
            if idx == 2:
                self.save_step(
                    step_index=4,
                    step_description=f"Validate the Second Journey, (T2), There should be a STOP message",
                    expected_result=f"STOP message found",
                    actual_result=f"STOP message found" if is_device_journey_end_found else "STOP message not found",
                    verdict=self.result_classifier.PASSED if is_device_journey_end_found else self.result_classifier.FAILED
                )

            self.logger.info(
                f"Test completed: Comparing two  different journeys end messages.")


class TRUMI_Devices_Comparision_Detection(BaseTestUtils):
    """Compare two HATI devices 
        Compare two HATI devices to see the journey status of both. 

        Procedure:
            - compare the journey messages of both devices.  (start, on the move, end)
        """

    def __init__(self):
        super().__init__()
        self.name = "TRUMI_Devices_Comparision_Detection"
        self.automation_content = "TRUMI_Devices_Comparision_Detection"
        self.description = "Tests detection and comparison of multiple HATI Devices"
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 1

    def teststeps(self):

        test_parameters = self.params_from_testcfg
        moving_speed_rpm = test_parameters.get("moving_speed_rpm")
        moving_time_sec = test_parameters.get("moving_time_sec")
        waiting_time_sec = test_parameters.get("waiting_time_sec")

       # ---> Step 1: Initiate Motion
        time_frames = self.initiate_motion_and_get_time_frames_for_the_duration(
            step_index=1,
            moving_speed_rpm=moving_speed_rpm,
            moving_time_sec=moving_time_sec,
            waiting_time_sec=waiting_time_sec,
            no_of_dut=len(self.DUT)
        )

        # ---> Build the data structure to record activities of the devices.
        dut_records = []

        for idx, dut in enumerate(self.DUT):
            dut_records.append({
                "index": idx,
                "dut": dut,
                "start_event": self._search_messages_for_device_location_start(time_frames[idx]),
                "on_the_move_event": self._search_messages_for_device_on_move(time_frames[idx]),
                "end_event": self._search_messages_for_device_journey_end(time_frames[idx])
            })

        self.logger.info(
            f"Device time-frame was retrieved successfully for the {len(dut_records)}")

        for step, record in enumerate(dut_records, start=2):
            dut = record["dut"]
            is_start, start_event = record["start_event"]
            is_on_the_move, on_the_move_event = record["on_the_move_event"]
            is_end, end_event = record["end_event"]

            if is_start and is_on_the_move and is_end:
                verdict = self.result_classifier.PASSED
            else:
                verdict = self.result_classifier.FAILED

            # start_text = "NO" if not is_start else f"YES."
            # on_the_move_text = "NO" if not is_on_the_move else f"YES."
            # end_text = "NO" if not is_end else f"YES."

            start_text = "No" if not is_start else f"Yes. ({start_event.get('messageDate')})"
            on_the_move_text = "No" if not is_on_the_move else f"Yes. ({on_the_move_event[0].get('messageDate')})"
            end_text = "No" if not is_end else f"Yes. ({end_event[0].get('messageDate')})"

            actual_result = f"""
                START: {start_text},\n
                ON THE MOVE: {on_the_move_text},\n
                END: {end_text}
                """

            self.logger.info(f"Checking the events for {dut.name}")
            self.logger.info(f"{actual_result}")

            self.save_step(
                step_index=step,
                step_description=f"Checking the events for {dut.name}",
                expected_result=f"Device events should indicate START, ON_THE_MOVE, STOP for the Drive duration",
                actual_result=actual_result,
                verdict=verdict
            )

        self.logger.info(f"Test completed: Comparing multiple devices")

    # def _debug_device_frame_fetch(self, dut):
    #     """Debug function to statistically fetch information from sensolus"""

        # TODO: Remove these print statements
        # print()
        # pprint(self.__dict__)
        # print()
        # for dut in self.DUT:
        #     pprint(dut.__dict__)
        #     print()
        # return

    #     start_time_utc = "2025-03-06T11:36:34"
    #     end_time_utc = "2025-03-06T11:59:34"

    #     messages = dut.get_frames(
    #         start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_frames=100)

    #     pprint(messages)

    #     for message in messages:
    #         for data in message["data"]:
    #             message_type = data["decodedMsg"].get("messageType")
    #             message_state = data["decodedMsg"].get("state")
    #             message_event = data["decodedMsg"].get("event")
    #             print(message_type, message_state, message_event)
