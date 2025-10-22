"""Test Suite for N5 Orientation Detection."""


import time
import datetime

from NSTAX.testscripts.test_script import TestScript


class OrientationDetectionBaseScript(TestScript):
    """Orientation Detection Functionality test base class.

    Pre-conditions:
        - xArm Robot Hand
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("XARM")

    def _get_orientation(self, payload):
        """Check the current orientation status"""
        try:
            current_orientation = payload["decodedMsg"]["payload"]["orientation"]["state"]
        except KeyError as e_:
            current_orientation = None
        return current_orientation

    def _if_orientation_status_message(self, payload):
        """Check if the current message returns orientation status"""
        try:
            is_od_status = payload["decodedMsg"]["payload"]["functionHeader"]["function"] == "ORIENTATION_DETECTION"
        except KeyError as e_:
            is_od_status = False
        return is_od_status

    def _get_current_ts_utc(self):
        current_timestamp_utc = datetime.datetime.strftime(datetime.datetime.utcnow(), "%Y-%m-%dT%H:%M:%S")
        return current_timestamp_utc


class AOD_ROSA_PF_RotationAngleThresholdsUnfolded(OrientationDetectionBaseScript):
    """Check the rotation angle thresholds for state UNFOLDED on ROSA Trolley.

    Pre-conditions:
        - An activated tracker with ORIENTATION_STATE_REPORTING_INTERVAL = 2 minutes
        - xArm robotic hand for orientation
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.name = "AOD_ROSA_PF_RotationAngleThresholdsUnfolded"
        self.automation_content = "AOD_ROSA_PF_RotationAngleThresholdsUnfolded"
        self.version = 0.1
        self.n_steps = 10

    def teststeps(self):
        # Step 1: Rotate to 35 degrees
        step_description = "Set angle to 35 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 1: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 275, 500, 500))     # 35 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(1, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 2: Read Status Messages. State: USED
        step_description = "Read Backend"
        expected_result = "Orientation Status = USED"
        actual_result = ""
        self.logger.info("Step 2: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "USED":
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 3: Rotate to 340 degrees
        step_description = "Set angle to 340 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 3: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 35, 500, 500))     # 340 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(3, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 4: Read Status Messages. State: UNKNOWN
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNKNOWN"
        actual_result = ""
        self.logger.info("Step 4: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNKNOWN":
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 5: Rotate to 0 degrees
        step_description = "Set angle to 0 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 5: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 135, 500, 500))     # 0 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(5, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 6: Read Status Messages. State: USED
        step_description = "Read Backend"
        expected_result = "Orientation Status = USED"
        actual_result = ""
        self.logger.info("Step 6: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "USED":
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 7: Rotate to 35 degrees
        step_description = "Set angle to 35 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 7: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 275, 500, 500))     # 35 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(7, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 8: Read Status Messages. State: USED, so no message
        step_description = "Read Backend"
        expected_result = "No Orientation Status Reporting"
        actual_result = ""
        self.logger.info("Step 8: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) != 0:
            actual_result = "Orientation Detection Status message received"
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 9: Rotate to 55 degrees
        step_description = "Set angle to 55 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 9: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 360, 500, 500))     # 55 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(9, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 10: Read Status Messages. State: UNUSED
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNUSED"
        actual_result = ""
        self.logger.info("Step 10: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNUSED":
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.FAILED)


class AOD_ROSA_PF_RotationAngleThresholdsFolded(OrientationDetectionBaseScript):
    """Check the rotation angle thresholds for state FOLDED on ROSA Trolley.

    Pre-conditions:
        - An activated tracker with ORIENTATION_STATE_REPORTING_INTERVAL = 2 minutes
        - xArm robotic hand for orientation
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.name = "AOD_ROSA_PF_RotationAngleThresholdsFolded"
        self.automation_content = "AOD_ROSA_PF_RotationAngleThresholdsFolded"
        self.version = 0.1
        self.n_steps = 10

    def teststeps(self):
        # Step 1: Rotate to 55 degrees
        step_description = "Set angle to 55 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 1: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 360, 500, 500))     # 55 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(1, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 2: Read Status Messages. State: UNUSED or Blank
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNUSED or No Report"
        actual_result = ""
        self.logger.info("Step 2: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            current_orientation = None
            actual_result = "No Status message received"
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            current_orientation = self._get_orientation(backend_messages[0])
            actual_result = f"Orientation Status: {current_orientation}"
            if current_orientation == "UNUSED":
                self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.PASSED)
            else:
                self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 3: Rotate to 35 degrees
        step_description = "Set angle to 35 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 3: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 275, 500, 500))     # 35 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(3, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 4: Read Status Messages. State: USED
        step_description = "Read Backend"
        expected_result = "Orientation Status = USED"
        actual_result = ""
        self.logger.info("Step 4: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "USED":
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 5: Rotate to 55 degrees
        step_description = "Set angle to 55 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 5: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 360, 500, 500))     # 55 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(5, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 6: Read Status Messages. State: UNUSED
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNUSED"
        actual_result = ""
        self.logger.info("Step 6: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNUSED":
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 7: Rotate to 90 degrees
        step_description = "Set angle to 90 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 7: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 500, 500, 500))     # 90 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(7, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 8: Read Status Messages. State: UNUSED, so no message
        step_description = "Read Backend"
        expected_result = "No Orientation Status Reporting"
        actual_result = ""
        self.logger.info("Step 8: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) != 0:
            actual_result = "Orientation Detection Status message received"
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 9: Rotate to 110 degrees
        step_description = "Set angle to 110 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 9: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 580, 500, 500))     # 110 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(9, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 10: Read Status Messages. State: UNKNOWN
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNKNOWN"
        actual_result = ""
        self.logger.info("Step 10: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNKNOWN":
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.FAILED)


class AOD_ROSA_PF_RotationAngleThresholdsUnknown(OrientationDetectionBaseScript):
    """Check the rotation angle thresholds for state UNKNOWN on ROSA Trolley.

    Pre-conditions:
        - An activated tracker with ORIENTATION_STATE_REPORTING_INTERVAL = 2 minutes
        - xArm robotic hand for orientation
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.name = "AOD_ROSA_PF_RotationAngleThresholdsUnknown"
        self.automation_content = "AOD_ROSA_PF_RotationAngleThresholdsUnknown"
        self.version = 0.1
        self.n_steps = 10

    def teststeps(self):
        # Step 1: Rotate to 180 degrees
        step_description = "Set angle to 180 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 1: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 860, 500, 500))     # 180 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(1, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 2: Read Status Messages. State: UNKNOWN
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNKNOWN"
        actual_result = ""
        self.logger.info("Step 2: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNKNOWN":
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 3: Rotate to 90 degrees
        step_description = "Set angle to 90 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 3: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 500, 500, 500))     # 90 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(3, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 4: Read Status Messages. State: UNUSED
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNUSED"
        actual_result = ""
        self.logger.info("Step 4: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNUSED":
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(4, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 5: Rotate to 110 degrees
        step_description = "Set angle to 110 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 5: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 580, 500, 500))     # 110 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(5, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 6: Read Status Messages. State: UNKNOWN
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNKNOWN"
        actual_result = ""
        self.logger.info("Step 6: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNKNOWN":
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(6, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 7: Rotate to 340 degrees
        step_description = "Set angle to 340 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 7: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 35, 500, 500))     # 340 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(7, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 8: Read Status Messages. State: UNKNOWN
        step_description = "Read Backend"
        expected_result = "Orientation Status = UNKNOWN"
        actual_result = ""
        self.logger.info("Step 8: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "UNKNOWN":
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(8, step_description, expected_result, actual_result, self.result_classifier.FAILED)

        # Step 9: Rotate to 0 degrees
        step_description = "Set angle to 0 degrees"
        expected_result = actual_result = ""
        t1 = self._get_current_ts_utc()
        self.logger.info("Step 9: %s", step_description)
        self.EQUIPMENT.set_position_raw((500, 500, 500, 135, 500, 500))     # 0 degrees
        # Wait 5 minutes
        time.sleep(300)
        self.save_step(9, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 10: Read Status Messages. State: USED
        step_description = "Read Backend"
        expected_result = "Orientation Status = USED"
        actual_result = ""
        self.logger.info("Step 10: %s", step_description)
        t2 = self._get_current_ts_utc()
        # GET backend messages
        backend_messages_t = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            # Catch only orientation detection status specific messages
            if self._if_orientation_status_message(message_):
                backend_messages.append(message_)
            else:
                continue
            backend_messages.append(message_)
        if len(backend_messages) < 1:
            actual_result = "No Orientation Detection Status message received"
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return
        else:
            current_orientation = self._get_orientation(backend_messages[0])
        actual_result = f"Orientation Status: {current_orientation}"
        if current_orientation == "USED":
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            self.save_step(10, step_description, expected_result, actual_result, self.result_classifier.FAILED)


if __name__ == "__main__":
    pass
