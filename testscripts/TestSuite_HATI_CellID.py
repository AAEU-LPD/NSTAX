"""Test Suite for HATI Cell ID Geolocation Feature."""

from NSTA.testscripts.test_script import TestScript
from NSTA.testscripts.lykaner_platform_message_v2 import PlatformMessage

from time import sleep
from datetime import datetime, timezone


class HATI_CellID_Utils():
    def __init__(self):
        pass

    def _check_location_message(messages):
        """Checks if a location message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if location msg is present)/False (if not present) + location Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            data = msg["data"]
            for d in data:
                message_type = d["decodedMsg"]["messageType"]
                if message_type == "LOCATION_UPDATE" or message_type == "WIFI_LOCATION":
                    return True, d
        return False, None
    
    def _check_trumi_message(messages):
        """Checks if a TRUMI based location message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if location msg is present)/False (if not present) + location Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            data = msg["data"]
            for d in data:
                message_type = d["decodedMsg"]["messageType"]
                if message_type == "LOCATION_UPDATE" or message_type == "WIFI_LOCATION":
                    message_state= d["decodedMsg"]["state"]
                    if message_state == "STOP":
                        return True, d
        return False, None
    
    def _check_cell_id(message, valid_locs):
        """Checks if the passed message has a cell ID that corresponds to an 
           assigned ID (valid cell ID)

        :param message: network message with cell ID
        :type message: dict
        :param valid_locs: list of valid cell IDs
        :type valid_locs: array
        :return: True(If cell ID matches valid IDs)/False(if no match found) + cell ID string
        :rtype: bool, str
        """
        cell_id = message["decodedMsg"].get("cellId", None)
        if cell_id is not None:
            if str(cell_id) in valid_locs:
                return True, cell_id
        return False, cell_id
    
    def _check_network_attach(message, set_operator="TEST"):
        """Checks if the operator assigned to the network message is from the assigned network

        :param message: network message with operator info
        :type message: dict
        :param set_operator: assigned network operator, defaults to "TEST"
        :type set_operator: str, optional
        :return: True(If network corresponds to set network operator)/False(If network is mismatched)
        :rtype: bool, str
        """
        operator = message["decodedMsg"].get("operatorInfo", None)
        if operator is not None:
            operator = message["decodedMsg"]["operatorInfo"]["brand"]
            if operator == set_operator:
                return True, operator
        return False, operator


class HATI_CellID_Cell_Attach(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID.
    
    This testcase uses the Profile Info config to trigger a periodic location message.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated has a periodic location message every 5-10 min
        - Device has Network location priority
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_CellID_Cell_Attach"
        self.automation_content = "[Automated] Cell ID Cell Attach"
        self.description = "Check Validity for CellID after attaching to an NB-IoT cell"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        ISOLATED_CELL_INDEX = test_parameters.get("isolated_cell_index")
        CELL_TYPE = test_parameters.get("cell_type")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()

        # Step 1: Retrieve cell number and set 2 cells to inactive state
        step_description = f"Cell Configuration: Keeping Cell_Number [{ISOLATED_CELL_INDEX}] active. Disabling other cells to check Cell Attach."
        expected_result = "Cells modified successfully"
        self.logger.info("Step 1: %s", step_description)
        cell_ids = callbox.get_cell_ids(CELL_TYPE)
        for cell in cell_ids:
            callbox.set_cell_gain(cell, -60)
        callbox.set_cell_gain(cell_ids[ISOLATED_CELL_INDEX], 0)
        actual_result = f"Setup successful. Starting Test."
        step_verdict = self.result_classifier.PASSED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)
        
        # Step 2: Wait for specified time and get latest messages from backend
        step_description = "Wait for specified time and get latest messages from backend"
        expected_result = "Received location message successfully."
        self.logger.info("Step 2: %s", step_description)
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        sleep((WAIT_TIME+1)*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        message_received, location_msg = HATI_CellID_Utils._check_location_message(backend_messages_t)
        if message_received:
            actual_result = f"Received location message successfully."
            step_verdict = self.result_classifier.PASSED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
            # Step 3: Check valid cell ID and UE attach
            step_description = "Evaluate cell ID locations"
            expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned network IDs)."
            self.logger.info("Step 3: %s", step_description)
            valid_locs = callbox.get_valid_cell_id_locations()
            cell_id_valid, cell_id_num = HATI_CellID_Utils._check_cell_id(location_msg, valid_locs)
            attach_valid, operator = HATI_CellID_Utils._check_network_attach(location_msg)
            if cell_id_valid and attach_valid:
                self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                actual_result = f"Cell ID ({cell_id_num}) is valid and corresponds to an assigned network Operator: {operator}."
                step_verdict = self.result_classifier.PASSED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach:{operator}")
                actual_result = f"Cell ID is invalid: {cell_id_num}, Attach:{operator}"
                step_verdict = self.result_classifier.FAILED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info("Test Failed! No location message received")
            actual_result = f"Did not receive a location message. Stopping Test."
            step_verdict = self.result_classifier.FAILED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
        # Step End: Return to default settings
        step_description = "Restore default settings to device"
        callbox.reset_cells_gain()               


class HATI_CellID_Cell_Attach_TRUMI(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID.
    
    This testcase uses the shaker to trigger a TRUMI location message.
       
    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated
        - Device has Network location priority 
        - Device is placed on a portable shaker
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_CellID_Cell_Attach_TRUMI"
        self.automation_content = "[Automated] Cell ID Cell Attach TRUMI"
        self.description = "Check Validity for CellID after attaching to an NB-IoT cell"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.requirement["EQUIPMENT"].append("NSTA25V")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        ISOLATED_CELL_INDEX = test_parameters.get("isolated_cell_index")
        SHAKE_TIME = test_parameters.get("shaker_duration_min")
        SHAKE_SPEED = test_parameters.get("shaker_speed_rpm")
        CELL_TYPE = test_parameters.get("cell_type")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
            if equ.name == "NSTA25V":
                shaker = equ
        callbox.reset_cells_gain()
        
        # Step 1: Retrieve cell number and set 2 cells to inactive state
        step_description = f"Cell Configuration: Keeping Cell_Number [{ISOLATED_CELL_INDEX}] active. Disabling other cells to check Cell Attach."
        expected_result = "Cells modified successfully"
        self.logger.info("Step 1: %s", step_description)
        cell_ids = callbox.get_cell_ids(CELL_TYPE)
        for cell in cell_ids:
            callbox.set_cell_gain(cell, -60)
        callbox.set_cell_gain(cell_ids[ISOLATED_CELL_INDEX], 0)
        actual_result = f"Setup successful. Starting Test."
        step_verdict = self.result_classifier.PASSED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)
        
        # Step 2: Wait for specified time and get latest messages from backend
        step_description = "Start portable shaker and wait to get message from device"
        expected_result = "Received location message successfully."
        self.logger.info("Step 2: %s", step_description)
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        self.logger.info(f"Shaking for {SHAKE_TIME} min")
        shaker.start_shaking()
        sleep((SHAKE_TIME)*60)
        shaker.stop_shaking()
        self.logger.info(f"Waiting for {WAIT_TIME} min to receive TRUMI-STOP message")
        sleep((WAIT_TIME+2)*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        message_received, location_msg = HATI_CellID_Utils._check_trumi_message(backend_messages_t)

        if message_received:
            actual_result = f"Received location message successfully."
            step_verdict = self.result_classifier.PASSED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
            # Step 3: Check valid cell ID and UE attach
            step_description = "Evaluate cell ID locations"
            expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned network IDs)."
            self.logger.info("Step 3: %s", step_description)
            valid_locs = callbox.get_valid_cell_id_locations()
            cell_id_valid, cell_id_num = HATI_CellID_Utils._check_cell_id(location_msg, valid_locs)
            attach_valid, operator = HATI_CellID_Utils._check_network_attach(location_msg)
            if cell_id_valid and attach_valid:
                self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                actual_result = "Cell ID ({cell_id_num}) is valid and corresponds to an assigned network Operator: {operator}."
                step_verdict = self.result_classifier.PASSED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach: {operator}")
                actual_result = f"Cell ID is invalid: {cell_id_num}, Attach: {operator}"
                step_verdict = self.result_classifier.FAILED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info("Test Failed! No TRUMI message received")
            actual_result = f"Did not receive a location message."
            step_verdict = self.result_classifier.FAILED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
        # Step End: Return to default settings
        step_description = "Restore default settings to device"
        callbox.reset_cells_gain()              
            
            
class HATI_CellID_Low_Service(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID
        in poor network conditions (service levels falling to low)
    
    This testcase uses the Profile Info config to trigger a periodic location messages.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated has a periodic location message every 5-10 min
        - Device has Network location priority
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_CellID_Low_Service"
        self.automation_content = "[Automated] Cell ID Low Service"
        self.description = "Check Validity for CellID in an NB-IoT cell with reducing service levels"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = -1
        self.version = 0.1
        
    def evaluate(self):
        """Result evaluation after test steps."""
        result = 0
        for index, result_step in self.result_step.items():
            result |= result_step["verdict"]
        # Current choice for calculating overall result:
        # RES_FAILED > RES_BLOCKED > RES_INCOMPLETE > RES_NOT_RUN > RES_PASSED
        if result & self.result_classifier.BLOCKED:
            result = self.result_classifier.BLOCKED
        elif result & self.result_classifier.INCOMPLETE:
            result = self.result_classifier.INCOMPLETE
        elif result & self.result_classifier.NOT_RUN:
            result = self.result_classifier.NOT_RUN
        elif result & self.result_classifier.PASSED:
            result = self.result_classifier.PASSED
        self.result = result
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        GAIN_RANGE = test_parameters.get("gain_range_dB")
        GAIN_STEP = test_parameters.get("gain_step_dB")
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        ISOLATED_CELL_INDEX = test_parameters.get("isolated_cell_index")
        CELL_TYPE = test_parameters.get("cell_type")
        FAIL_COUNT = 0
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        n = 1
        # Step n + 1: Retrieve cell number and set 2 cells to inactive state
        step_description = f"Cell Configuration: Keeping Cell_Number [{ISOLATED_CELL_INDEX}] active. Disabling other cells to check Cell Attach in reducing service levels."
        expected_result = f"Cells modified successfully."
        self.logger.info("Step %d: %s",n,step_description)
        cell_ids = callbox.get_cell_ids(CELL_TYPE)
        for cell in cell_ids:
            callbox.set_cell_gain(cell, -60)
        callbox.set_cell_gain(cell_ids[ISOLATED_CELL_INDEX], 0)
        actual_result = f"Setup successful. Starting Test."
        step_verdict = self.result_classifier.PASSED
        self.save_step(n, step_description, expected_result, actual_result, step_verdict)
        for gain_value in range(GAIN_RANGE[0], GAIN_RANGE[1] - GAIN_STEP, - GAIN_STEP):   
            if FAIL_COUNT == 1:
                # Reset Cell gain to zero and wait for location message to avoid device going into timeout
                self.logger.info(f"Waiting {WAIT_TIME} minutes for device to restore connection.")
                callbox.set_cell_gain(cell_ids[ISOLATED_CELL_INDEX], 0)
                start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                sleep((WAIT_TIME+1)*60)
                end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
                message_received, location_msg = HATI_CellID_Utils._check_location_message(backend_messages_t)
                if not message_received:
                    break
            if FAIL_COUNT >= 2:
                break 
            # Step n + 1: Retrieve cell number and set 2 cells to inactive state
            step_description = f"Cell Configuration: reducing cell gain."
            expected_result = f"Cells modified successfully, Isolated cell is set to gain:{gain_value}"
            self.logger.info("Step %d: %s",n+1,step_description)
            callbox.set_cell_gain(cell_ids[ISOLATED_CELL_INDEX], gain_value)
            actual_result = f"Setup successful. Starting Test."
            step_verdict = self.result_classifier.PASSED
            self.save_step(n+1, step_description, expected_result, actual_result, step_verdict)
            
            # Step n + 2: Wait for specified time and get latest messages from backend
            step_description = "Wait for specified time and get latest messages from backend"
            expected_result = "Received location message successfully."
            self.logger.info("Step %d: %s",n+2,step_description)
            start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            sleep((WAIT_TIME+1)*60)
            end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
            message_received, location_msg = HATI_CellID_Utils._check_location_message(backend_messages_t)
            if message_received:
                actual_result = f"Received location message successfully."
                step_verdict = self.result_classifier.PASSED
                self.save_step(n+2, step_description, expected_result, actual_result, step_verdict)
                
                # Step n + 3: Check valid cell ID and UE attach
                step_description = "Evaluate cell ID locations"
                expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned callbox IDs)."
                self.logger.info("Step %d: %s",n+3,step_description)
                valid_locs = callbox.get_valid_cell_id_locations()
                cell_id_valid, cell_id_num = HATI_CellID_Utils._check_cell_id(location_msg, valid_locs)
                attach_valid, operator = HATI_CellID_Utils._check_network_attach(location_msg)
                if cell_id_valid and attach_valid:
                    self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                    actual_result = f"Cell ID ({cell_id_num}) is valid and corresponds to an assigned network Operator: {operator}."
                    step_verdict = self.result_classifier.PASSED
                    self.save_step(n+3, step_description, expected_result, actual_result, step_verdict)
                else:
                    self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach:{operator}")
                    actual_result = f"Cell ID is invalid: {cell_id_num}, Attach:{operator}"
                    step_verdict = self.result_classifier.FAILED
                    self.save_step(n+3, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info("Lost connection to network! No location message received")
                actual_result = f"Did not receive a location message. Possible loss of connection to network."
                step_verdict = self.result_classifier.FAILED
                self.save_step(n+2, step_description, expected_result, actual_result, step_verdict)
                FAIL_COUNT += 1
            n += 3
            
        # Step End: Return to default settings
        step_description = "Restore default settings to device"
        callbox.reset_cells_gain()               
            
            
class HATI_CellID_Reconnection_Cell_Switch(TestScript):
    """Validate device is able to reconnect to the Nb-IOT network through a different cell
       on loss of service and obtain a valid cell_ID

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated has a periodic location message every 5-10 min
        - Device has Network location priority
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_CellID_Reconnection_Cell_Switch"
        self.automation_content = "[Automated] Cell ID Reconnection Cell Switch"
        self.description = "Check Validity for CellID in an NB-IoT cell switching scenario on loss of service"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        ISOLATED_CELLS_INDEX = test_parameters.get("isolated_cell_index")
        CELL_TYPES = test_parameters.get("cell_types")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()
        # Step 1: Retrieve cell number and set 2 cells to inactive state
        step_description = f"Cell Configuration: Keeping Cell_Number [{ISOLATED_CELLS_INDEX[0]} active. Disabling other cells."
        expected_result = f"Cells modified successfully. Cell {ISOLATED_CELLS_INDEX[0]} active."
        self.logger.info("Step %d: %s",1,step_description)
        cell_ids = callbox.get_cell_ids(CELL_TYPES[0])
        for cell in cell_ids:
            callbox.set_cell_gain(cell, -60)
        callbox.set_cell_gain(cell_ids[ISOLATED_CELLS_INDEX[0]], 0)
        actual_result = f"Setup successful. Starting Test."
        step_verdict = self.result_classifier.PASSED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)
        
        # Step 2: Wait for specified time and get latest messages from backend
        step_description = "Wait for specified time and get latest messages from backend"
        expected_result = "Received location message successfully."
        self.logger.info("Step %d: %s",2,step_description)
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        sleep((WAIT_TIME+1)*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        message_received, location_msg = HATI_CellID_Utils._check_location_message(backend_messages_t)
        if message_received:
            actual_result = f"Received location message successfully."
            step_verdict = self.result_classifier.PASSED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
            # Step 3: Check valid cell ID and UE attach
            step_description = "Evaluate cell ID locations"
            expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned callbox IDs)."
            self.logger.info("Step %d: %s",3,step_description)
            valid_locs = callbox.get_valid_cell_id_locations()
            cell1_id_valid, cell1_id_num = HATI_CellID_Utils._check_cell_id(location_msg, valid_locs)
            attach1_valid, operator1 = HATI_CellID_Utils._check_network_attach(location_msg)
            if cell1_id_valid and attach1_valid:
                self.logger.info(f"Cell ID is valid: {cell1_id_num}, Operator: {operator1}")
                actual_result = f"Cell ID ({cell1_id_num}) is valid and corresponds to an assigned network Operator: {operator1}"
                step_verdict = self.result_classifier.PASSED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info(f"Cell ID is invalid: {cell1_id_num}, Attach:{operator1}")
                actual_result = f"Cell ID is invalid: {cell1_id_num}, Attach:{operator1}"
                step_verdict = self.result_classifier.FAILED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info("Test Failed: No location message received")
            actual_result = f"Did not receive a location message"
            step_verdict = self.result_classifier.FAILED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
        # Step 4: Retrieve cell number and set 2 cells to inactive state
        step_description = f"Cell Configuration: Keeping Cell_Number [{ISOLATED_CELLS_INDEX[1]} active. Disabling other cells."
        expected_result = f"Cells modified successfully. Cell {ISOLATED_CELLS_INDEX[1]} active."
        self.logger.info("Step %d: %s",4,step_description)
        cell_ids = callbox.get_cell_ids(CELL_TYPES[1])
        for cell in cell_ids:
            callbox.set_cell_gain(cell, -60)
        callbox.set_cell_gain(cell_ids[ISOLATED_CELLS_INDEX[1]], 0)
        actual_result = f"Setup successful. Starting Test."
        step_verdict = self.result_classifier.PASSED
        self.save_step(4, step_description, expected_result, actual_result, step_verdict)
        
        # Step 5: Wait for specified time and get latest messages from backend
        step_description = "Wait for specified time and get latest messages from backend"
        expected_result = "Received location message successfully."
        self.logger.info("Step %d: %s",5,step_description)
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        sleep((WAIT_TIME+1)*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        message_received, location_msg = HATI_CellID_Utils._check_location_message(backend_messages_t)
        if message_received:
            actual_result = f"Received location message successfully."
            step_verdict = self.result_classifier.PASSED
            self.save_step(5, step_description, expected_result, actual_result, step_verdict)
            
            # Step 6: Check valid cell ID and UE attach
            step_description = "Evaluate cell ID locations"
            expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned callbox IDs)."
            self.logger.info("Step %d: %s",6,step_description)
            valid_locs = callbox.get_valid_cell_id_locations()
            cell2_id_valid, cell2_id_num = HATI_CellID_Utils._check_cell_id(location_msg, valid_locs)
            attach2_valid, operator2 = HATI_CellID_Utils._check_network_attach(location_msg)
            if cell2_id_valid and attach2_valid:
                self.logger.info(f"Cell ID is valid: {cell2_id_num}, Operator: {operator2}")
                actual_result = f"Cell ID ({cell2_id_num}) is valid and corresponds to an assigned network Operator: {operator2}"
                step_verdict = self.result_classifier.PASSED
                self.save_step(6, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info(f"Cell ID is invalid: {cell2_id_num}, Attach:{operator2}")
                actual_result = f"Cell ID is invalid: {cell2_id_num}, Attach:{operator2}"
                step_verdict = self.result_classifier.FAILED
                self.save_step(6, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info("Lost connection to network! No location message received")
            actual_result = f"Did not receive a location message. Possible loss of connection to network."
            step_verdict = self.result_classifier.FAILED
            self.save_step(5, step_description, expected_result, actual_result, step_verdict)
            
        # Step 7: Confirm cell ID changed and switched from Cell 1 to Cell 2
        step_description = "Confirm Cell Switching by comparing Cell IDs"
        expected_result = "Cell ID successfully switched from Cell 1 to Cell 2"
        self.logger.info("Step %d: %s",7,step_description)  
        if cell1_id_num != cell2_id_num:
            self.logger.info(f"Cell 1 ID: {cell2_id_num}, Cell 2 ID: {cell2_id_num}. Cell IDs have switched!")
            actual_result = f"Cell IDs are valid and successfully switched from Cell 1 to Cell 2"
            step_verdict = self.result_classifier.PASSED
            self.save_step(7, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info(f"Cell 1 ID: {cell2_id_num}, Cell 2 ID: {cell2_id_num}. Cell IDs did not switch.")
            actual_result = f"Cell IDs are valid but did not switch from Cell 1 to Cell 2"
            step_verdict = self.result_classifier.FAILED
            self.save_step(7, step_description, expected_result, actual_result, step_verdict)
            
        # Step End: Return to default settings
        step_description = "Restore default settings to device"
        callbox.reset_cells_gain()               
            
            
class HATI_CellID_Cell_Attach_Custom(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID.
    The valid cell IDs are evaluated against provided cell ID in the test_config.yaml
    
    This testcase uses the Profile Info config to trigger a periodic location messages.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated has a periodic location message every 5-10 min
        - Device has Network location priority
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_CellID_Cell_Attach_Custom"
        self.automation_content = "[Automated] Cell ID Cell Attach Custom"
        self.description = "Check Validity for CellID after attaching to an NB-IoT cell (Provided Cell IDs in config)"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 2
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        CELL_IDS = test_parameters.get("cell_ids")
        OPERATOR = test_parameters.get("operator")   
        
        # Step 1: Wait for specified time and get latest messages from backend
        step_description = "Wait for specified time and get latest messages from backend"
        expected_result = "Received location message successfully."
        self.logger.info("Step 1: %s", step_description)
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        sleep((WAIT_TIME+1)*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        message_received, location_msg = HATI_CellID_Utils._check_location_message(backend_messages_t)
        if message_received:
            actual_result = f"Received location message successfully."
            step_verdict = self.result_classifier.PASSED
            self.save_step(1, step_description, expected_result, actual_result, step_verdict)
            
            # Step 2: Check valid cell ID and UE attach
            step_description = "Evaluate cell ID locations"
            expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned network IDs)."
            self.logger.info("Step 2: %s", step_description)
            cell_id_valid, cell_id_num = HATI_CellID_Utils._check_cell_id(location_msg, CELL_IDS)
            attach_valid, operator = HATI_CellID_Utils._check_network_attach(location_msg, OPERATOR)
            if cell_id_valid and attach_valid:
                self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                actual_result = f"Cell ID ({cell_id_num}) is valid and corresponds to an assigned network Operator: {operator}."
                step_verdict = self.result_classifier.PASSED
                self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach:{operator}")
                actual_result = f"Cell ID is invalid: {cell_id_num}, Attach:{operator}"
                step_verdict = self.result_classifier.FAILED
                self.save_step(2, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info("Test Failed! No location message received")
            actual_result = f"Did not receive a location message. Stopping Test."
            step_verdict = self.result_classifier.FAILED
            self.save_step(1, step_description, expected_result, actual_result, step_verdict)

