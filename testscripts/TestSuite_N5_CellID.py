"""Test Suite for N5 Cell ID Geolocation Feature."""

from NSTAX.testscripts.test_script import TestScript
from NSTAX.testscripts.lykaner_platform_message_v2 import PlatformMessage


class N5_CellID_BasePerfStats(TestScript):
    """Check basic performance stats of the Cell Id feature of platform device.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.name = "N5_CellID_BasePerfStats"
        self.automation_content = "N5_CellID_BasePerfStats"
        self.description = "Check Valid CellIDs for Journey Relevant Messages of N5"
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 3
        self.version = 0.1

    def teststeps(self):
        # Step 0: Get test parameters
        test_parameters = self.params_from_testcfg
        start_time_utc = test_parameters.get("start_time_utc")
        end_time_utc = test_parameters.get("end_time_utc")
        max_message_count = test_parameters.get("max_message_count")

        # Step 1: Retrieve device messages from platform
        step_description = "Retrieve platform messages"
        expected_result = "#messages_received > 10"
        self.logger.info("Step 1: %s", step_description)
        backend_messages_t = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_messages=max_message_count)
        n_messages = len(backend_messages_t)
        actual_result = f"#messages_received: {n_messages}"
        step_verdict = self.result_classifier.PASSED if n_messages > 10 else self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        # Retrieve successful cell id transmitted in STATUS and WIFI messages
        status_messages = []
        n_messages_status = 0
        n_valid_net_locations_status = 0
        n_invalid_net_locations_status = 0
        wifi_messages = []
        n_messages_wifi = 0
        n_valid_net_locations_wifi = 0
        n_invalid_net_locations_wifi = 0
        for message_ in backend_messages_t:
            try:
                message_type = message_["decodedMsg"]["messageType"]
            except KeyError:
                message_type = ""
            try:
                alps_message_type = message_["decodedMsg"]["payload"]["alpsMessageType"]
            except KeyError:
                alps_message_type = ""
            try:
                message_state = message_["decodedMsg"]["state"]
            except KeyError:
                message_state = ""
            if alps_message_type == "STATUS_NORMAL":
                # Status message due to start of a journey
                status_messages.append(message_.copy())
            elif message_type == "ALPS_WIFI_EXTENDED":
                wifi_messages.append(message_.copy())
        n_messages_status = len(status_messages)
        n_messages_wifi = len(wifi_messages)
        for status_message in status_messages:
            raw_payload = status_message["rawMsg"]["dataDecoded"]
            decoded_payload = PlatformMessage(raw_payload)
            if decoded_payload.NET_LOC_VALID:
                n_valid_net_locations_status += 1
            else:
                n_invalid_net_locations_status += 1
        for wifi_message in wifi_messages:
            raw_payload = wifi_message["rawMsg"]["dataDecoded"]
            decoded_payload = PlatformMessage(raw_payload)
            if decoded_payload.NET_LOC_VALID:
                n_valid_net_locations_wifi += 1
            else:
                n_invalid_net_locations_wifi += 1

        # Step 2: Valid Network Locations over STATUS_NORMAL
        step_description = "Valid Network Locations over STATUS_NORMAL"
        expected_result = "#valid_locations > 80%"
        self.logger.info("Step 2: %s", step_description)
        if n_messages_status > 0:
            valid_locations_p = int(100 * n_valid_net_locations_status / n_messages_status)
            step_verdict = self.result_classifier.PASSED if valid_locations_p > 80 else self.result_classifier.FAILED
            actual_result = f"#valid_locations: {valid_locations_p}% ({n_valid_net_locations_status} / {n_messages_status})"
        else:
            step_verdict = self.result_classifier.NOT_RUN
            actual_result = "no status messages received"
        self.save_step(2, step_description, expected_result, actual_result, step_verdict)

        # Step 3: Valid Network Locations over ALPS_WIFI_EXTENDED
        step_description = "Valid Network Locations over ALPS_WIFI_EXTENDED"
        expected_result = "#valid_locations > 80%"
        self.logger.info("Step 3: %s", step_description)
        if n_messages_wifi > 0:
            valid_locations_p = int(100 * n_valid_net_locations_wifi / n_messages_wifi)
            step_verdict = self.result_classifier.PASSED if valid_locations_p > 80 else self.result_classifier.FAILED
            actual_result = f"#valid_locations: {valid_locations_p}% ({n_valid_net_locations_wifi} / {n_messages_wifi})"
        else:
            step_verdict = self.result_classifier.NOT_RUN
            actual_result = "no status messages received"
        self.save_step(3, step_description, expected_result, actual_result, step_verdict)

from time import sleep
from datetime import datetime, timezone

class N5_CellID_Utils():
    def __init__(self):
        pass

    def _check_wifi_message(messages):
        """Checks if a WiFi location message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if WiFi msg is present)/False (if not present) + WiFi Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            data = msg["data"]
            for d in data:
                message_type = d["decodedMsg"]["messageType"]
                if message_type == "ALPS_WIFI_EXTENDED":
                    return True, msg
        return False, None
    
    def _check_trumi_message(messages):
        """Checks if a TRUMI based WiFi location message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if WiFi msg is present)/False (if not present) + WiFi Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            data = msg["data"]
            for d in data:
                message_type = d["decodedMsg"]["messageType"]
                if message_type == "ALPS_WIFI_EXTENDED":
                    message_state= d["decodedMsg"]["state"]
                    if message_state == "STOP":
                        return True, msg
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
        net_msgs = message["data"] # change to data message
        for n in net_msgs:
            cell_id = n["decodedMsg"]["header"]["cellId"]
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
        net_msgs = message["networks"]
        for n in net_msgs:
            operator = n["decodedMsg"]["operatorInfo"]["brand"]
            if operator == set_operator:
                return True, operator
        return False, operator


class N5_CellID_Cell_Attach(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID.
    
    This testcase uses the Profile Info config to trigger a periodic WiFi location messages.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated and has a downlink every 10 min
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "N5_CellID_Cell_Attach"
        self.automation_content = "N5_CellID_Cell_Attach"
        self.description = "Check Validity for CellID after attaching to an NB-IoT cell"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        CELL_TYPE = test_parameters.get("cell_type")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        response = self.DUT.push_downlink_payload("b007814000000005","KA_5min")
        if response:
            self.logger.info("Waiting for 10 mins to receive next WiFi message.")
            sleep((10+2)*60)
            end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
            message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
            
            if message_received:
                # Step 1: Retrieve cell number and set 2 cells to inactive state
                step_description = "Disable 2 out of 3 cells to keep 1 Active cell to check Cell Attach."
                expected_result = "Cells modified successfully, 1 cell active out of 3"
                self.logger.info("Step 1: %s", step_description)
                cell_ids = callbox.get_cell_ids(CELL_TYPE)
                for cell in cell_ids:
                    callbox.set_cell_gain(cell, -60)
                callbox.set_cell_gain(cell_ids[0], 0)
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
                message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
                if message_received:
                    actual_result = f"Received location message successfully."
                    step_verdict = self.result_classifier.PASSED
                    self.save_step(2, step_description, expected_result, actual_result, step_verdict)
                    
                    # Step 3: Check valid cell ID and UE attach
                    step_description = "Evaluate cell ID locations"
                    expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned network IDs)."
                    self.logger.info("Step 3: %s", step_description)
                    valid_locs = callbox.get_valid_cell_id_locations()
                    cell_id_valid, cell_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, valid_locs)
                    attach_valid, operator = N5_CellID_Utils._check_network_attach(wifi_msg)
                    if cell_id_valid and attach_valid:
                        self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                        actual_result = f"Cell ID ({cell_id_num}) is valid and corresponds to an assigned network ID"
                        step_verdict = self.result_classifier.PASSED
                        self.save_step(3, step_description, expected_result, actual_result, step_verdict)
                    else:
                        self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach:{operator}")
                        actual_result = f"Cell ID is invalid: {cell_id_num}, Attach:{operator}"
                        step_verdict = self.result_classifier.FAILED
                        self.save_step(3, step_description, expected_result, actual_result, step_verdict)
                else:
                    self.logger.info("Test Failed! No wifi message received")
                    actual_result = f"Did not receive a wifi location message. Stopping Test."
                    step_verdict = self.result_classifier.FAILED
                    self.save_step(2, step_description, expected_result, actual_result, step_verdict)
                    
                # Step End: Return to default settings
                step_description = "Restore default settings to device"
                callbox.reset_cells_gain()               
                response = self.DUT.push_downlink_payload("b00794c000000009","KA_24hrs")
            else:
                err = "Message not found during waiting time. Test setup Failed. Stopping test."
                self.logger.info(err)
                raise Exception (err)
        else:
            err = "Error in communicating with backend. Test setup Failed. Stopping test."
            self.logger.info(err)
            raise Exception (err)


class N5_CellID_Cell_Attach_TRUMI(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID.
    
    This testcase uses the shaker to trigger a TRUMI WiFi location message.
       
    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated
        - Device is placed on a portable shaker
    """
    def __init__(self):
        super().__init__()
        self.name = "N5_CellID_Cell_Attach_TRUMI"
        self.automation_content = "N5_CellID_Cell_Attach_TRUMI"
        self.description = "Check Validity for CellID after attaching to an NB-IoT cell"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.requirement["EQUIPMENT"].append("IKAKS130")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        SHAKE_TIME = test_parameters.get("shaker_duration_min")
        SHAKE_SPEED = test_parameters.get("shaker_speed_rpm")
        CELL_TYPE = test_parameters.get("cell_type")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
            if equ.name == "IKAKS130":
                shaker = equ
        callbox.reset_cells_gain()
        
        # Step 1: Retrieve cell numbers and set 2 cells to inactive state
        step_description = "Disable 2 out of 3 cells to keep 1 Active cell check Cell Attach."
        expected_result = "Cells modified successfully, 1 cell active out of 3"
        self.logger.info("Step 1: %s", step_description)
        cell_ids = callbox.get_cell_ids(CELL_TYPE)
        for cell in cell_ids:
            callbox.set_cell_gain(cell, -60)
        callbox.set_cell_gain(cell_ids[0], 0)
        actual_result = f"Setup successful. Starting Test."
        step_verdict = self.result_classifier.PASSED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)
        
        # Step 2: Wait for specified time and get latest messages from backend
        step_description = "Start portable shaker and wait to get message from device"
        expected_result = "Received location message successfully."
        self.logger.info("Step 2: %s", step_description)
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        self.logger.info(f"Shaking at {SHAKE_SPEED} for {SHAKE_TIME} min")
        shaker.start_shaking(SHAKE_SPEED)
        sleep((SHAKE_TIME)*60)
        shaker.stop()
        self.logger.info(f"Waiting for {WAIT_TIME} min to receive TRUMI-STOP message")
        sleep((WAIT_TIME+2)*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        message_received, wifi_msg = N5_CellID_Utils._check_trumi_message(backend_messages_t)
        if message_received:
            actual_result = f"Received location message successfully."
            step_verdict = self.result_classifier.PASSED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
            # Step 3: Check valid cell ID and UE attach
            step_description = "Evaluate cell ID locations"
            expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned network IDs)."
            self.logger.info("Step 3: %s", step_description)
            valid_locs = callbox.get_valid_cell_id_locations()
            cell_id_valid, cell_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, valid_locs)
            attach_valid, operator = N5_CellID_Utils._check_network_attach(wifi_msg)
            if cell_id_valid and attach_valid:
                self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                actual_result = "Cell ID ({cell_id_num}) is valid and corresponds to an assigned network ID"
                step_verdict = self.result_classifier.PASSED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
            else:
                self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach: {operator}")
                actual_result = f"Cell ID is invalid: {cell_id_num}, Attach: {operator}"
                step_verdict = self.result_classifier.FAILED
                self.save_step(3, step_description, expected_result, actual_result, step_verdict)
        else:
            self.logger.info("Test Failed! No TRUMI message received")
            actual_result = f"Did not receive a wifi location message."
            step_verdict = self.result_classifier.FAILED
            self.save_step(2, step_description, expected_result, actual_result, step_verdict)
            
        # Step End: Return to default settings
        step_description = "Restore default settings to device"
        callbox.reset_cells_gain()              
            
            
class N5_CellID_Low_Service(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID
        in poor network conditions (service levels falling to low)
    
    This testcase uses the Profile Info config to trigger a periodic WiFi location messages.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated and has a downlink every 10 min
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "N5_CellID_Low_Service"
        self.automation_content = "N5_CellID_Low_Service"
        self.description = "Check Validity for CellID in an NB-IoT cell with reducing service levels"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        GAIN_RANGE = test_parameters.get("gain_range_dB")
        GAIN_STEP = test_parameters.get("gain_step_dB")
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        CELL_TYPE = test_parameters.get("cell_type")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        response = self.DUT.push_downlink_payload("b007814000000005","KA_5min")
        if response:
            self.logger.info("Waiting for 10 mins to receive next WiFi message.")
            sleep((10+2)*60)
            end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
            message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
            
            if message_received:
                n = 0
                for gain_value in range(GAIN_RANGE[0], GAIN_RANGE[1] - GAIN_STEP, - GAIN_STEP):    
                    # Step n + 1: Retrieve cell number and set 2 cells to inactive state
                    step_description = "Disable 2 out of 3 cells to keep 1 Active cell check Cell Attach in reducing service levels."
                    expected_result = f"Cells modified successfully, 1 cell active out of 3 and set to gain:{gain_value}"
                    self.logger.info("Step %d: %s",n+1,step_description)
                    cell_ids = callbox.get_cell_ids(CELL_TYPE)
                    for cell in cell_ids:
                        callbox.set_cell_gain(cell, -60)
                    callbox.set_cell_gain(cell_ids[0], gain_value)
                    actual_result = f"Setup successful. Starting Test."
                    step_verdict = self.result_classifier.PASSED
                    self.save_step(n+1, step_description, expected_result, actual_result, step_verdict)
                    
                    # Step n + 2: Wait for specified time and get latest messages from backend
                    step_description = "Set waiting time and getting latest messages"
                    expected_result = "Received location message successfully."
                    self.logger.info("Step %d: %s",n+2,step_description)
                    start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                    sleep((WAIT_TIME+1)*60)
                    end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
                    backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
                    message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
                    if message_received:
                        actual_result = f"Received location message successfully."
                        step_verdict = self.result_classifier.PASSED
                        self.save_step(n+2, step_description, expected_result, actual_result, step_verdict)
                        
                        # Step n + 3: Check valid cell ID and UE attach
                        step_description = "Evaluate cell ID locations"
                        expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned callbox IDs)."
                        self.logger.info("Step %d: %s",n+3,step_description)
                        valid_locs = callbox.get_valid_cell_id_locations()
                        cell_id_valid, cell_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, valid_locs)
                        attach_valid, operator = N5_CellID_Utils._check_network_attach(wifi_msg)
                        if cell_id_valid and attach_valid:
                            self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                            actual_result = f"Cell ID ({cell_id_num}) is valid and corresponds to an assigned network ID"
                            step_verdict = self.result_classifier.PASSED
                            self.save_step(n+3, step_description, expected_result, actual_result, step_verdict)
                        else:
                            self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach:{operator}")
                            actual_result = f"Cell ID is invalid: {cell_id_num}, Attach:{operator}"
                            step_verdict = self.result_classifier.FAILED
                            self.save_step(n+3, step_description, expected_result, actual_result, step_verdict)
                    else:
                        self.logger.info("Lost connection to network! No wifi message received")
                        actual_result = f"Did not receive a wifi location message. Possible loss of connection to network."
                        step_verdict = self.result_classifier.PASSED
                        self.save_step(n+2, step_description, expected_result, actual_result, step_verdict)
                    n += 3
                    
                # Step End: Return to default settings
                step_description = "Restore default settings to device"
                callbox.reset_cells_gain()               
                response = self.DUT.push_downlink_payload("b00794c000000009","KA_24hrs")
            else:
                err = "Message not found during waiting time. Test setup Failed. Stopping test."
                self.logger.info(err)
                raise Exception (err)
        else:
            err = "Error in communicating with backend. Test setup Failed. Stopping test."
            self.logger.info(err)
            raise Exception (err)
            
            
class N5_CellID_Reconnection_Cell_Switch(TestScript):
    """Validate device is able to reconnect to the Nb-IOT network through a different cell
       on loss of service and obtain a valid cell_ID

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated and has a downlink every 10 min
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "N5_CellID_Reconnection_Cell_Switch"
        self.automation_content = "N5_CellID_Reconnection_Cell_Switch"
        self.description = "Check Validity for CellID in an NB-IoT cell switching scenario on loss of service"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        CELL_TYPES = test_parameters.get("cell_types")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        response = self.DUT.push_downlink_payload("b007814000000005","KA_5min")
        if response:
            self.logger.info("Waiting for 10 mins to receive next WiFi message.")
            sleep((10+2)*60)
            end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
            message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
            
            if message_received:
                # Step 1: Retrieve cell number and set 2 cells to inactive state
                step_description = "Confirming attach to Cell 1. Disable rest of the 2 out of 3 cells"
                expected_result = f"Cells modified successfully, 1st cell active out of 3"
                self.logger.info("Step %d: %s",1,step_description)
                cell_ids = callbox.get_cell_ids(CELL_TYPES[0])
                for cell in cell_ids:
                    callbox.set_cell_gain(cell, -60)
                callbox.set_cell_gain(cell_ids[0], 0)
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
                message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
                if message_received:
                    actual_result = f"Received location message successfully."
                    step_verdict = self.result_classifier.PASSED
                    self.save_step(2, step_description, expected_result, actual_result, step_verdict)
                    
                    # Step 3: Check valid cell ID and UE attach
                    step_description = "Evaluate cell ID locations"
                    expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned callbox IDs)."
                    self.logger.info("Step %d: %s",3,step_description)
                    valid_locs = callbox.get_valid_cell_id_locations()
                    cell1_id_valid, cell1_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, valid_locs)
                    attach1_valid, operator1 = N5_CellID_Utils._check_network_attach(wifi_msg)
                    if cell1_id_valid and attach1_valid:
                        self.logger.info(f"Cell ID is valid: {cell1_id_num}, Operator: {operator1}")
                        actual_result = f"Cell ID ({cell1_id_num}) is valid and corresponds to an assigned network ID"
                        step_verdict = self.result_classifier.PASSED
                        self.save_step(3, step_description, expected_result, actual_result, step_verdict)
                    else:
                        self.logger.info(f"Cell ID is invalid: {cell1_id_num}, Attach:{operator1}")
                        actual_result = f"Cell ID is invalid: {cell1_id_num}, Attach:{operator1}"
                        step_verdict = self.result_classifier.FAILED
                        self.save_step(3, step_description, expected_result, actual_result, step_verdict)
                else:
                    self.logger.info("Test Failed: No wifi message received")
                    actual_result = f"Did not receive a wifi location message"
                    step_verdict = self.result_classifier.FAILED
                    self.save_step(2, step_description, expected_result, actual_result, step_verdict)
                    
                # Step 4: Retrieve cell number and set 2 cells to inactive state
                step_description = "Confirming attach to Cell 2. Disable rest of the 2 out of 3 cells"
                expected_result = f"Cells modified successfully, 2nd cell active out of 3"
                self.logger.info("Step %d: %s",4,step_description)
                cell_ids = callbox.get_cell_ids(CELL_TYPES[1])
                for cell in cell_ids:
                    callbox.set_cell_gain(cell, -60)
                callbox.set_cell_gain(cell_ids[1], 0)
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
                message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
                if message_received:
                    actual_result = f"Received location message successfully."
                    step_verdict = self.result_classifier.PASSED
                    self.save_step(5, step_description, expected_result, actual_result, step_verdict)
                    
                    # Step 6: Check valid cell ID and UE attach
                    step_description = "Evaluate cell ID locations"
                    expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned callbox IDs)."
                    self.logger.info("Step %d: %s",6,step_description)
                    valid_locs = callbox.get_valid_cell_id_locations()
                    cell2_id_valid, cell2_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, valid_locs)
                    attach2_valid, operator2 = N5_CellID_Utils._check_network_attach(wifi_msg)
                    if cell2_id_valid and attach2_valid:
                        self.logger.info(f"Cell ID is valid: {cell2_id_num}, Operator: {operator2}")
                        actual_result = f"Cell ID ({cell2_id_num}) is valid and corresponds to an assigned network ID"
                        step_verdict = self.result_classifier.PASSED
                        self.save_step(6, step_description, expected_result, actual_result, step_verdict)
                    else:
                        self.logger.info(f"Cell ID is invalid: {cell2_id_num}, Attach:{operator2}")
                        actual_result = f"Cell ID is invalid: {cell2_id_num}, Attach:{operator2}"
                        step_verdict = self.result_classifier.FAILED
                        self.save_step(6, step_description, expected_result, actual_result, step_verdict)
                else:
                    self.logger.info("Lost connection to network! No wifi message received")
                    actual_result = f"Did not receive a wifi location message. Possible loss of connection to network."
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
                response = self.DUT.push_downlink_payload("b00794c000000009","KA_24hrs")
            else:
                err = "Message not found during waiting time. Test setup Failed. Stopping test."
                self.logger.info(err)
                raise Exception (err)
        else:
            err = "Error in communicating with backend. Test setup Failed. Stopping test."
            self.logger.info(err)
            raise Exception (err)
            
            
### NEW TEST CASE: CELL ID CUSTOM (VALIDATE AGAINST GIVEN CELL IDS IN CONFIG
class N5_CellID_Cell_Attach_Custom(TestScript):
    """Validate device is able to connect to the Nb-IOT network and obtain a valid cell_ID.
    The valid cell IDs are evaluated against provided cell ID in the test_config.yaml
    
    This testcase uses the Profile Info config to trigger a periodic WiFi location messages.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated and has a downlink every 10 min
        - Amarisoft callbox accessable through SSH
    """
    def __init__(self):
        super().__init__()
        self.name = "N5_CellID_Cell_Attach_Custom"
        self.automation_content = "N5_CellID_Cell_Attach_Custom"
        self.description = "Check Validity for CellID after attaching to an NB-IoT cell (Provided Cell IDs in config)"
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.n_steps = 3
        self.version = 0.1
        
    def teststeps(self):
        test_parameters = self.params_from_testcfg
        WAIT_TIME = test_parameters.get("message_wait_interval_min")
        CELL_IDS = test_parameters.get("cell_ids")
        OPERATOR = test_parameters.get("operator")
        
        # Step X: Setup Equipment and Devices
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
        callbox.reset_cells_gain()
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        response = self.DUT.push_downlink_payload("b007814000000005","KA_5min")
        if response:
            self.logger.info("Waiting for 10 mins to receive next WiFi message.")
            sleep((10+2)*60)
            end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
            backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
            message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
            
            if message_received:
                # Step 1: Retrieve cell number and set 2 cells to inactive state
                step_description = "Disable 2 out of 3 cells to keep 1 Active cell to check Cell Attach."
                expected_result = "Cells modified successfully, 1 cell active out of 3"
                self.logger.info("Step 1: %s", step_description)
                cell_ids = callbox.get_cell_ids(CELL_TYPE)
                for cell in cell_ids:
                    callbox.set_cell_gain(cell, -60)
                callbox.set_cell_gain(cell_ids[0], 0)
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
                message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
                if message_received:
                    actual_result = f"Received location message successfully."
                    step_verdict = self.result_classifier.PASSED
                    self.save_step(2, step_description, expected_result, actual_result, step_verdict)
                    
                    # Step 3: Check valid cell ID and UE attach
                    step_description = "Evaluate cell ID locations"
                    expected_result = "Cell ID is valid (non-zero or FFFFFF and corresponds to assigned network IDs)."
                    self.logger.info("Step 3: %s", step_description)
                    cell_id_valid, cell_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, CELL_IDS)
                    attach_valid, operator = N5_CellID_Utils._check_network_attach(wifi_msg, OPERATOR)
                    if cell_id_valid and attach_valid:
                        self.logger.info(f"Cell ID is valid: {cell_id_num}, Operator: {operator}")
                        actual_result = f"Cell ID ({cell_id_num}) is valid and corresponds to an assigned network ID"
                        step_verdict = self.result_classifier.PASSED
                        self.save_step(3, step_description, expected_result, actual_result, step_verdict)
                    else:
                        self.logger.info(f"Cell ID is invalid: {cell_id_num}, Attach:{operator}")
                        actual_result = f"Cell ID is invalid: {cell_id_num}, Attach:{operator}"
                        step_verdict = self.result_classifier.FAILED
                        self.save_step(3, step_description, expected_result, actual_result, step_verdict)
                else:
                    self.logger.info("Test Failed! No wifi message received")
                    actual_result = f"Did not receive a wifi location message. Stopping Test."
                    step_verdict = self.result_classifier.FAILED
                    self.save_step(2, step_description, expected_result, actual_result, step_verdict)
                    
                # Step End: Return to default settings
                step_description = "Restore default settings to device"
                callbox.reset_cells_gain()               
                response = self.DUT.push_downlink_payload("b00794c000000009","KA_24hrs")
            else:
                err = "Message not found during waiting time. Test setup Failed. Stopping test."
                self.logger.info(err)
                raise Exception (err)
        else:
            err = "Error in communicating with backend. Test setup Failed. Stopping test."
            self.logger.info(err)
            raise Exception (err)


### TEST CODE TO GET MESSAGES ###
# start_time_utc = "2024-08-30T12:20:40"
# end_time_utc = "2024-08-30T12:25:45"

# backend_messages_t = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
# print(backend_messages_t)
# message_received, wifi_msg = N5_CellID_Utils._check_wifi_message(backend_messages_t)
# valid_locs = ['25646439', '25636297', '26059978', '26059977']
# cell_id_valid, cell_id_num = N5_CellID_Utils._check_cell_id(wifi_msg, valid_locs)
# print(cell_id_valid)
# print(cell_id_num)