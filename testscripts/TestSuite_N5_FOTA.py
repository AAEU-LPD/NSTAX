"""Test Suite for N5 Firmware Over The Air Update (FOTA)."""

import time
import datetime
import re

from NSTAX.testscripts.test_script import TestScript


class FOTABaseScript(TestScript):
    """Base test script for FOTA Suite.
       includes common mettods, 
    """
    def __init__(self):
        super().__init__()

    def _get_current_ts_utc(self):
        current_timestamp_utc = datetime.datetime.strftime(datetime.datetime.utcnow(),"%Y-%m-%dT%H:%M:%S")
        return current_timestamp_utc
    
    def _get_FW_parts(self, firmware_version):

        regex_str = r"FWUP_PKG_LYKN5_ALPS_(Prod|Debug)_(.+)?_v(\d+)\.(\d+).(\d+)"
        match = re.match(regex_str, firmware_version)

        if match:
           int_fw_version_major = int(match.group(3))
           int_fw_version_minor = int(match.group(4))
           fw_git_sha = str(match.group(2))
           str_fw_git_sha = fw_git_sha[:-2]
           version = {
                "fw_version_major":  int_fw_version_major,
                "fw_version_minor": int_fw_version_minor,
                "fw_git_sha": str_fw_git_sha
            }

        else:
            self.logger.error("Falling parsing firmware version name:")
            raise Exception ("falling parsing firmware version name")

        return version
    
    def _check_FW_version_(self, version, boot_message):

        int_fw_version_major = version["fw_version_major"]
        int_fw_version_minor = version["fw_version_minor"]
        str_fw_git_sha = version["fw_git_sha"]

        if boot_message:
            try:
                fw_version_major = boot_message["decodedMsg"]["fwVersionMajor"]
                fw_version_minor = boot_message["decodedMsg"]["fwVersionMinor"]
                fw_git_sha = boot_message["decodedMsg"]["gitSha"]
            except KeyError as error:
                self.logger.error("falling accessing to boot message info error: %s" , error )
                fw_version_major = fw_version_minor = fw_git_sha = None

        if fw_version_major == int_fw_version_major and fw_version_minor == int_fw_version_minor and fw_git_sha == str_fw_git_sha:
            return True
        
        return False
    
    def _check_DL_command_ack(self, time_start, time_window_size, payload_to_validate):

        for i in range(time_window_size):
             self.logger.info("waiting to confirm dl command , time in minutes: %s", i)
             time.sleep(60)

        time_end = self._get_current_ts_utc()      
        backend_messages = self.DUT.get_messages(start_time_utc=time_start, 
                                                     end_time_utc = time_end, 
                                                     max_n_messages=150)
        backend_messages.reverse()
        dl_request_check = False
        result = False

        # check the for the message sequence 
        for idx, message_ in enumerate(backend_messages):
            if message_["decodedMsg"]["messageType"] == "ALPS_STATUS" and message_["decodedMsg"]["payload"]["alpsMessageType"] == 'STATUS_DOWNLINK_REQUEST' and message_["downlinkMsg"]["payload"] == payload_to_validate.upper():
                dl_request_check = True

            if message_["decodedMsg"]["messageType"] == "BIDIR_ACK" and message_["decodedMsg"]["command"] == 'OK' and dl_request_check:
                result = True
                break

            else:
                result = False

        return result



class FOTA_StandardOperation(FOTABaseScript):
    """Perform FOTA on a single tracker.

    Purpose of this test is to check if FOTA operation is being performed in the
    expected manner, for a single update in a single tracker.

    Pre-conditions:
        - An activated tracker FOTA enabled FW
        - Access to AlpsAlpine API Platform (sensolous)
    """
    def __init__(self):
        super().__init__()
        self.name = "FOTA_StandardOperation"
        self.automation_content = "FOTA_StandardOperation"
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 3

    def teststeps(self):

        test_parameters = self.params_from_testcfg
        FW_candidate = test_parameters.get('FW_candidate')
        FW_version_parts = self._get_FW_parts(FW_candidate)      
    
        # Step 1: Queue the FW candidate to the backend
        step_description = f"Queue FW: {FW_candidate}"
        expected_result = "FW Queued"
        actual_result = ""
        self.logger.info("Step 1: %s", step_description)
        post_status = self.DUT.queue_firmware(FW_candidate)
        t1 = self._get_current_ts_utc()
        if post_status:
            # Queueing successful
            actual_result = "FW Queued"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result = "FW Queueing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        # Step 2: Wait 60 minutes
        step_description = "Wait 60 minutes"
        expected_result = actual_result = ""
        self.logger.info("Step 2: %s", step_description)
        time.sleep(3600)
        #time.sleep(1)
        self.save_step(2, step_description, expected_result, actual_result, self.result_classifier.PASSED)

        # Step 3: Check backend for boot messages
        step_description = "Check Backend for Boot Messages"
        expected_result = "Boot Message Visible"
        actual_result = ""
        self.logger.info("Step 3: %s", step_description)
        # Read Backend
        t2 = self._get_current_ts_utc()
        boot_message = None
        backend_messages = self.DUT.get_messages(start_time_utc=t1, end_time_utc = t2, max_n_messages=150)
        for message_ in backend_messages:
            if message_["decodedMsg"]["messageType"] == "NBIOT_BOOT":
                boot_message = message_.copy()
                break
        if boot_message:
            actual_result = "Boot Message Visible"
            self.save_step(3, step_description, expected_result, actual_result, self.result_classifier.PASSED)
        else:
            actual_result = "No Boot Message Visible"
            self.save_step(3, step_description, expected_result, actual_result, self.result_classifier.FAILED)
            self.logger.error("Step failed, skipping remaining steps")
            return

        # Step 4: Check boot message contents for FW version validation 
        step_description = "Check FW Version (major/minor/sha)"
        expected_result = "Correct FW Loaded"
        actual_result = ""
        self.logger.info("Step 4: %s", step_description)
        
        if (self._check_FW_version_(FW_version_parts, boot_message)):
            actual_result = "Correct FW Loaded"
            step_verdict = self.result_classifier.PASSED
        else:
            actual_result = "Wrong FW info in loop:"
            step_verdict = self.result_classifier.FAILED
            
        self.save_step(4, step_description, expected_result, actual_result, step_verdict)


class FOTA_Loop(FOTABaseScript):
    """ Performs several FOTA updates on a single tracker.

    Purpose of this test is to check if FOTA opertion is being performed in the
    expected manner.

    Pre-conditions:
        - flash a device with a capable FOTA firmware
        - your should have access to sensolous backend
        - test config file sould provide.
            firmware candidate 
            number of loops 
            duration of loop
    """

    def __init__(self):
        super().__init__()
        self.name = "FOTA_Loop"
        self.automation_content = "FOTA_Loop" 
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        #self.number_of_loops = 3
        #self.n_steps = 1 + (4 * self.number_of_loops)
        
    def initialize(self):        
        test_parameters = self.params_from_testcfg
        self.number_of_loops = test_parameters.get('number_of_loops')
        self.n_steps = 1 + (4 * self.number_of_loops)
        super().initialize()


    def teststeps(self):
        # parameters
        test_parameters = self.params_from_testcfg
        FW_candidate = test_parameters.get('FW_candidate')
        FW_version_parts = self._get_FW_parts(FW_candidate)
        duration_of_loop = test_parameters.get('duration_of_loop_min')  

        #------------- device configuration -------------
        step_description = "Setting DL Frecuency to 10 Min"
        expected_result = "Configuration set to DL 10 min"

        payload = "b007c2800000000e"
        description = "test_DL_every_10_min"
        dl_request = self.DUT.push_downlink_payload(payload,description)
        if dl_request:
            actual_result = "Configuration set to DL 10 min"
            step_verdict = self.result_classifier.PASSED
        else:
            actual_result = "Configuration not set"
            step_verdict = self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

   
        #-------------- Push FOTA in LOOP---------------------------
        last_step  = 1

        for loop in range(self.number_of_loops):
            
            step = last_step + 1
            # STEP Clear current queue
            step_description ="Firmware upgrade queue cleared"
            expected_result = "Queue Cleared"
            actual_result = ""
            post_status = self.DUT.clear_queue_firmware_upgrade()
            if post_status:
                # Queue cleaned
                actual_result = "Queue Cleared for loop: " + str(loop)
                step_verdict = self.result_classifier.PASSED
            else:
                # Issue with queueing
                actual_result =  "Queue Clearing Failed for loop: "  + str(loop)
                step_verdict = self.result_classifier.FAILED
            self.save_step(step, step_description, expected_result, actual_result, step_verdict)

            # STEP Queue the FW candidate to the backend
            step += 1
            step_description = f"Queue FW: {FW_candidate}"
            expected_result = "FW Queued"
            actual_result = ""
            post_status = self.DUT.queue_firmware(FW_candidate)
            t1 = self._get_current_ts_utc()
            if post_status:
                # Queueing successful
                actual_result = f"FW Queued for loop: " + str(loop)
                step_verdict = self.result_classifier.PASSED
            else:
                # Issue with queueing
                actual_result = f"FW Queueing Failed for loop" + str(loop)
                step_verdict = self.result_classifier.FAILED
            self.save_step( step, step_description, expected_result, actual_result, step_verdict)

            # Wait x time, to check that FOTA Happened
            
            for i in range(duration_of_loop):
                self.logger.info("waiting, time in minutes: %s", i)
                # TODO remove next print, only activated for debug purposes
                # print(str(i))
                time.sleep(60)

            # STEP Read backend for boot messages
            step += 1
            step_description = "Check Backend for Boot Messages"
            expected_result = "Boot Message Visible"
            actual_result = ""
            self.logger.info("Step: %s", step_description)
            t2 = self._get_current_ts_utc()
            #t1 = '2023-10-26T19:17:05'
            #t2 = '2023-10-26T21:17:05'
            boot_message = None
            backend_messages = self.DUT.get_messages(start_time_utc=t1, 
                                                     end_time_utc = t2, 
                                                     max_n_messages=150)
            
            for idx, message_ in enumerate(backend_messages):
                # check the first message sequence 
                if message_["decodedMsg"]["messageType"] == "NBIOT_BOOT":
                    boot_message = message_.copy()
                    message_2 = backend_messages[idx -1]
                    if message_2["decodedMsg"]["messageType"] == "ALPS_STATUS" and message_2["decodedMsg"]["payload"]["alpsMessageType"] == 'STATUS_OTA' and message_2["decodedMsg"]["payload"]["provisionalStatus"] == 'PROVISIONAL':
                        # save time to disocunt it later
                        time_FOTA_provisional =  message_2["decodedMsg"]["header"]["messageGenerationTime"]
                        is_message_provisional_present = True
                        break
                    
            if boot_message:
                actual_result = "Boot Message Visible in loop: " + str(loop)
                step_verdict = self.result_classifier.PASSED
            else:
                actual_result = "No Boot Message Visible in loop: "+  str(loop)
                step_verdict = self.result_classifier.FAILED

            self.save_step(step, step_description,
                               expected_result,
                               actual_result,
                               step_verdict)

            # STEP Check boot message contents
            step += 1
            step_description = "Check FW Version (major/minor/sha)"
            expected_result = "Correct FW Loaded"
            actual_result = ""           
            self.logger.info("Step: %s", step_description)

            if (self._check_FW_version_(FW_version_parts, boot_message)):
                actual_result = "Correct FW Loaded in loop: " + str(loop)
                step_verdict = self.result_classifier.PASSED
            else:
                actual_result = "Wrong FW info in loop: " + str(loop)
                step_verdict = self.result_classifier.FAILED
            self.save_step(step, step_description, expected_result, actual_result, step_verdict)

            # Check from provicional time, if the curren time is shorter than 1 hour wait until complete this time to start next loop 

            # Formating time 
            time_now = self._get_current_ts_utc()
            #time_now = '2023-10-26T21:19:05'
            date_format = "%Y-%m-%dT%H:%M:%S"
            time_now = datetime.datetime.strptime(time_now,date_format)
            date_format = "%Y-%m-%dT%H:%M:%S%z"
            time_FOTA_provisional = datetime.datetime.strptime(time_FOTA_provisional,date_format)
            time_FOTA_provisional = time_FOTA_provisional.replace(tzinfo=None)
            
            
            pending_time = time_now - time_FOTA_provisional
            
            if pending_time.seconds > 0 :
                minutes_to_wait = int(pending_time.seconds / 60)
                for i in range(minutes_to_wait):
                     self.logger.info("waiting for provisioning time in minutes: remaining time %s", minutes_to_wait - i)
                     time.sleep(60)

            last_step = step

class FOTA_provision_time(FOTABaseScript):
    
    """Perform FOTA on a single tracker, and validates provisioning time messages  

    Pre-conditions:
        - flash a device, but don't activate it
        - Access to AlpsAlpine API Platform
        - test config file sould provide.
            firmware candidate 
            duration of loop
    """
    def __init__(self):
        super().__init__()
        self.name = "FOTA_provision_time"
        self.automation_content = "FOTA_provision_time" 
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 4

                
    def teststeps(self):

        test_parameters = self.params_from_testcfg
        FW_candidate = test_parameters.get('FW_candidate')
        FW_version_parts = self._get_FW_parts(FW_candidate)
        duration_of_loop = test_parameters.get('duration_of_loop_min')  

        #------------- device configuration -------------
        step_description = "Setting DL Frecuency to 10 Min"
        expected_result = "Configuration set to DL 10 min"

        payload = "b007c2800000000e"
        description = "test_DL_every_10_min"
        dl_request = self.DUT.push_downlink_payload(payload,description)
        if dl_request:
            print (" DL configuration performed")
            actual_result = "Configuration set to DL 10 min"
            step_verdict = self.result_classifier.PASSED
        else:
            print (" DL configuration Failed ")
            actual_result = "Configuration not set"
            step_verdict = self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        #-------------- Push FOTA ---------------------------

        # STEP Clear current queue

        step_description ="Firmware upgrade queue cleared"
        expected_result = "Queue Cleared"
        actual_result = ""
        post_status = self.DUT.clear_queue_firmware_upgrade()
        if post_status:
            # Queue cleaned
            actual_result = "Queue Cleared"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result =  "Queue Clearing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(2, step_description, expected_result, actual_result, step_verdict)

        # STEP Queue the FW candidate to the backend

        expected_result = "FW Queued"
        step_description = f"Queue FW: {FW_candidate}"
        actual_result = ""
        post_status = self.DUT.queue_firmware(FW_candidate)
        t1 = self._get_current_ts_utc()
        if post_status:
            # Queueing successful
            actual_result = "FW Queued"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result = "FW Queueing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(3, step_description, expected_result, actual_result, step_verdict)

        ## Wait x time, to check that FOTA Happened
            
        for i in range(duration_of_loop):
             self.logger.info("waiting, time in minutes: %s", i)
             time.sleep(60)
        
        # STEP Read backend for boot messages
        
        t2 = self._get_current_ts_utc()
        backend_messages = self.DUT.get_messages(start_time_utc=t1,
                                                 end_time_utc = t2,
                                                 max_n_messages=200)
        
        ## validates the sequence of messages for Provisioning messages and firmware version 

        step_description ="FOTA provision sequence present"
        expected_result = "FOTA provision messages present and delta time equal to 3600 seconds"
        actual_result = ""

        is_message_provisional_present = False
        is_message_valid_present = False
        is_correct_FW_present = False

        for idx, message_ in enumerate(backend_messages):
            # check for the second message secuence         
            if message_["decodedMsg"]["messageType"] == "ALPS_STATUS" and message_["decodedMsg"]["payload"]["alpsMessageType"]  == 'STATUS_OTA' and message_["decodedMsg"]["payload"]["provisionalStatus"] == 'VALID':
                time_FOTA_valid =  message_["decodedMsg"]["header"]["messageGenerationTime"]
                is_message_valid_present = True
            # check the first message sequence 
            if message_["decodedMsg"]["messageType"] == "NBIOT_BOOT":
                if (self._check_FW_version_(FW_version_parts, message_)):
                    is_correct_FW_present = True
                message_2 = backend_messages[idx -1]
                # TODO validate firmware version
                if message_2["decodedMsg"]["messageType"] == "ALPS_STATUS" and message_2["decodedMsg"]["payload"]["alpsMessageType"] == 'STATUS_OTA' and message_2["decodedMsg"]["payload"]["provisionalStatus"] == 'PROVISIONAL':
                    # save time to disocunt it later
                    time_FOTA_provisional =  message_2["decodedMsg"]["header"]["messageGenerationTime"]
                    is_message_provisional_present = True


            if is_message_provisional_present and is_message_valid_present and is_correct_FW_present:
                # TODO discount time of messages,  # validate it is only hour after  
                date_format = "%Y-%m-%dT%H:%M:%S%z"
                time_FOTA_provisional = datetime.datetime.strptime(time_FOTA_provisional,date_format)
                time_FOTA_valid = datetime.datetime.strptime(time_FOTA_valid,date_format)
                time_FOTA_provision_delta = time_FOTA_valid - time_FOTA_provisional
                # validating time delta for FOTA provision 1 hour
                if time_FOTA_provision_delta.seconds == 3600 :
                    actual_result = "FOTA provision messages present and delta time equal to 3600 seconds: " + str(time_FOTA_provision_delta.seconds)
                    step_verdict = self.result_classifier.PASSED
                else:
                    actual_result = "Status FOTA provision time delta Fail, time in seconds: " + str(time_FOTA_provision_delta.seconds)
                break                    
            
            actual_result = f"FOTA provision time failed.  Provisional message status: {is_message_provisional_present}, Valid message status: {is_message_valid_present}, FW version status: {is_correct_FW_present}."   
            step_verdict = self.result_classifier.FAILED
        self.save_step(4, step_description, expected_result, actual_result, step_verdict)


class FOTA_previous_FW(FOTABaseScript):
    """attemps to Perform  FOTA on a single tracker using a previous FW version.

    Purpose of this test is to check that FOTA opertion is not performed .

    Pre-conditions:
        - flash a device with newer fw version
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.name = "FOTA_previous_FW"
        self.automation_content = "FOTA_previous_FW" 
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 5

                
    def teststeps(self):

        test_parameters = self.params_from_testcfg
        FW_candidate = test_parameters.get('FW_candidate')
        FW_version_parts = self._get_FW_parts(FW_candidate)
        duration_of_loop = test_parameters.get('duration_of_loop_min')  

         #------------- device configuration -------------
        step_description = "Setting DL Frecuency to 10 Min"
        expected_result = "Configuration set to DL 10 min"

        payload = "b007c2800000000e"
        description = "test_DL_every_10_min"
        dl_request = self.DUT.push_downlink_payload(payload,description)
        if dl_request:
            print (" DL configuration performed")
            actual_result = "Configuration set to DL 10 min"
            step_verdict = self.result_classifier.PASSED
        else:
            print (" DL configuration Failed ")
            actual_result = "Configuration not set"
            step_verdict = self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        #-------------- Push FOTA ---------------------------

        # STEP Clear current queue

        step_description ="Firmware upgrade queue cleared"
        expected_result = "Queue Cleared"
        actual_result = ""
        post_status = self.DUT.clear_queue_firmware_upgrade()
        if post_status:
            # Queue cleaned
            actual_result = "Queue Cleared"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result =  "Queue Clearing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(2, step_description, expected_result, actual_result, step_verdict)

        # STEP Queue the FW candidate to the backend

        expected_result = "FW Queued"
        step_description = f"Queue FW: {FW_candidate}"
        actual_result = ""
        post_status = self.DUT.queue_firmware(FW_candidate)
        t1 = self._get_current_ts_utc()
        if post_status:
            # Queueing successful
            actual_result = "FW Queued"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result = "FW Queueing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(3, step_description, expected_result, actual_result, step_verdict)

            # Wait x time, to check that FOTA Happened
            
        for i in range(duration_of_loop):
            self.logger.info("waiting, time in minutes: %s", i)
            time.sleep(60)
        
        # STEP Queue the FW candidate to the backend

        t2 = self._get_current_ts_utc()
        backend_messages = self.DUT.get_messages(start_time_utc=t1,
                                                     end_time_utc = t2,
                                                     max_n_messages=150)
        
        # validates the sequence of messages when a FOTA is attempted in a previous fw version 

        step_description ="Firmware upgrade not performed"
        expected_result = "FOTA blocking sequence present"
        actual_result = ""

        for idx, message_ in enumerate(backend_messages):
            if message_["decodedMsg"]["messageType"] == "UNDECODABLE":
                message_2 = backend_messages[idx +1]
                if message_2["decodedMsg"]["messageType"] == "FOTA" and message_2["decodedMsg"]["action"] == 'START':
                    message_3 = backend_messages[idx +2]
                    if message_3["decodedMsg"]["messageType"] == "FOTA" and message_3["decodedMsg"]["action"] == 'REQUEST_FILE_INFO':
                        print("fota failed ok")
                        actual_result = "FOTA blocking sequence present"
                        step_verdict = self.result_classifier.PASSED
                        break
            actual_result = "FOTA blocking sequence NOT present"
            step_verdict = self.result_classifier.FAILED
        self.save_step(4, step_description, expected_result, actual_result, step_verdict)

          # STEP Clear current queue

        step_description ="Firmware upgrade queue cleared"
        expected_result = "Queue Cleared"
        actual_result = ""
        post_status = self.DUT.clear_queue_firmware_upgrade()
        if post_status:
            # Queue cleaned
            actual_result = "Queue Cleared"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result =  "Queue Clearing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(5, step_description, expected_result, actual_result, step_verdict)



class FOTA_corrupted_FW(FOTABaseScript):
    """attemps to Perform  FOTA on a single tracker using a corrupted FW version.

    Purpose of this test is to check that FOTA operation is not performed .

    Pre-conditions:
        - flash a device with fota capable FW version
        - Access to AlpsAlpine API Platform
    """
    def __init__(self):
        super().__init__()
        self.name = "FOTA_corrupted_FW"
        self.automation_content = "FOTA_corrupted_FW" 
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 5

                
    def teststeps(self):

        test_parameters = self.params_from_testcfg
        FW_candidate = test_parameters.get('FW_candidate')
        FW_version_parts = self._get_FW_parts(FW_candidate)
        duration_of_loop = test_parameters.get('duration_of_loop_min')  


         #------------- device configuration -------------
        step_description = "Setting DL Frecuency to 10 Min"
        expected_result = "Configuration set to DL 10 min"

        payload = "b007c2800000000e"
        description = "test_DL_every_10_min"
        dl_request = self.DUT.push_downlink_payload(payload,description)
        if dl_request:
            print (" DL configuration performed")
            actual_result = "Configuration set to DL 10 min"
            step_verdict = self.result_classifier.PASSED
        else:
            print (" DL configuration Failed ")
            actual_result = "Configuration not set"
            step_verdict = self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        #-------------- Push FOTA ---------------------------

        # STEP Clear current queue

        step_description ="Firmware upgrade queue cleared"
        expected_result = "Queue Cleared"
        actual_result = ""
        post_status = self.DUT.clear_queue_firmware_upgrade()
        if post_status:
            # Queue cleaned
            actual_result = "Queue Cleared"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result =  "Queue Clearing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(2, step_description, expected_result, actual_result, step_verdict)

        # STEP Queue the FW candidate to the backend

        expected_result = "FW Queued"
        step_description = f"Queue FW: {FW_candidate}"
        actual_result = ""
        post_status = self.DUT.queue_firmware(FW_candidate)
        t1 = self._get_current_ts_utc()
        if post_status:
            # Queueing successful
            actual_result = "FW Queued"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result = "FW Queueing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(3, step_description, expected_result, actual_result, step_verdict)

            # Wait x time, to check that FOTA Happened
            
        for i in range(duration_of_loop):
            self.logger.info("waiting, time in minutes: %s", i)
            time.sleep(60)
        
        # STEP obtainig messages from backend

        t2 = self._get_current_ts_utc()
        backend_messages = self.DUT.get_messages(start_time_utc=t1,
                                                     end_time_utc = t2,
                                                     max_n_messages=150)
        
        # validates the sequence of messages when a FOTA is attempted in a corrupted FW version 

        step_description ="Firmware upgrade not performed"
        expected_result = "Corrupted firmware blocking sequence present"
        actual_result = ""

        for idx, message_ in enumerate(backend_messages):
            if message_["decodedMsg"]["messageType"] == "UNDECODABLE":
                message_2 = backend_messages[idx +1]
                if message_2["decodedMsg"]["messageType"] == "FOTA" and message_2["decodedMsg"]["action"] == 'START':
                    message_3 = backend_messages[idx +2]
                    if message_3["decodedMsg"]["messageType"] == "FOTA" and message_3["decodedMsg"]["action"] == 'REQUEST_FILE_INFO':
                        print("fota failed ok")
                        actual_result = "Corrupted firmware blocking sequence present"
                        step_verdict = self.result_classifier.PASSED
                        break
            actual_result = "Corrupted firmware blocking sequence NOT present"
            step_verdict = self.result_classifier.FAILED
        self.save_step(4, step_description, expected_result, actual_result, step_verdict)


        # STEP Clear current queue

        step_description ="Firmware upgrade queue cleared"
        expected_result = "Queue Cleared"
        actual_result = ""
        post_status = self.DUT.clear_queue_firmware_upgrade()
        if post_status:
            # Queue cleaned
            actual_result = "Queue Cleared"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result =  "Queue Clearing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(5, step_description, expected_result, actual_result, step_verdict)



class FOTA_config_retention(FOTABaseScript):
    
    """Perform FOTA and validates that retains previous settings
    - b007c2800000000e N5_GENERIC_NORMAL_DOWNLINK_PERIOD: 10_minutes
    - b00782800000000a N5_GENERIC_KEEP_ALIVE_SEND_INTERVAL: 10_minutes

    Pre-conditions:
        - flash a device, but don't activate it
        - Access to AlpsAlpine API Platform
        - test config file sould provide.
            firmware candidate 
            duration of loop
    """
    def __init__(self):
        super().__init__()
        self.name = "FOTA_config_retention"
        self.automation_content = "FOTA_config_retention" 
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 4

                
    def teststeps(self):

        test_parameters = self.params_from_testcfg
        FW_candidate = test_parameters.get('FW_candidate')
        FW_version_parts = self._get_FW_parts(FW_candidate)
        duration_of_loop = test_parameters.get('duration_of_loop_min')  

        # STEP ------------- device configuration -------------
        step_description = "Setting DL Frecuency to 10 Min"
        expected_result = "Configuration set to DL 10 min"

        payload = "b007c2800000000e"
        description = "test_DL_every_10_min"
        time_start_step_1 = self._get_current_ts_utc()
        dl_request = self.DUT.push_downlink_payload(payload,description)
        if dl_request:
            print (" DL configuration performed")
            actual_result = "Configuration set to DL 10 min"
            step_verdict = self.result_classifier.PASSED
        else:
            print (" DL configuration Failed ")
            actual_result = "Configuration not set"
            step_verdict = self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)


        # STEP ------------- verify command ------------------

        step_description = "Check for ACK in Donwlink configuration message"
        expected_result = "DL ACK configuration accepted"

        if self._check_DL_command_ack(time_start_step_1, 30, payload ):
            actual_result = "DL ACK configuration accepted"
            step_verdict = self.result_classifier.PASSED
        else:
            actual_result = "Configuration not accepted, ACK not present" 
            step_verdict = self.result_classifier.FAILED

        self.save_step(2, step_description,
                               expected_result,
                               actual_result,
                               step_verdict)



        # STEP ------------- device configuration -------------
        step_description = "Setting Keep alive Frecuency to 10 Min"
        expected_result = "keep alive Configuration set to DL 10 min"

        payload = "b00782800000000a"
        description = "test_keep_alive_every_10_min"
        time_start_step_3 = self._get_current_ts_utc()
        dl_request = self.DUT.push_downlink_payload(payload,description)
        if dl_request:
            print (" Keep alive configuration performed")
            actual_result = "Configuration set to DL 10 min"
            step_verdict = self.result_classifier.PASSED
        else:
            print (" Keep alive configuration Failed ")
            actual_result = "Configuration not set"
            step_verdict = self.result_classifier.FAILED
        self.save_step(3, step_description, expected_result, actual_result, step_verdict)

        
        # STEP ------------- verify command ------------------

        step_description = "Check for ACK in Donwlink configuration message"
        expected_result = "DL ACK configuration accepted"

        if self._check_DL_command_ack(time_start_step_3, 30, payload ):
            actual_result = "DL ACK configuration accepted"
            step_verdict = self.result_classifier.PASSED
        else:
            actual_result = "Configuration not accepted, ACK not present" 
            step_verdict = self.result_classifier.FAILED

        self.save_step(4, step_description,
                               expected_result,
                               actual_result,
                               step_verdict)



        # STEP ------------- Clear current queue ----------------

        step_description ="Firmware upgrade queue cleared"
        expected_result = "Queue Cleared"
        actual_result = ""
        post_status = self.DUT.clear_queue_firmware_upgrade()
        if post_status:
            # Queue cleaned
            actual_result = "Queue Cleared"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result =  "Queue Clearing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(5, step_description, expected_result, actual_result, step_verdict)

        # STEP -------- Queue the FW candidate to the backend ----------

        expected_result = "FW Queued"
        step_description = f"Queue FW: {FW_candidate}"
        actual_result = ""
        post_status = self.DUT.queue_firmware(FW_candidate)
        t1 = self._get_current_ts_utc()
        if post_status:
            # Queueing successful
            actual_result = "FW Queued"
            step_verdict = self.result_classifier.PASSED
        else:
            # Issue with queueing
            actual_result = "FW Queueing Failed"
            step_verdict = self.result_classifier.FAILED
        self.save_step(6, step_description, expected_result, actual_result, step_verdict)

        # Wait x time, to check that FOTA Happened
            
        for i in range(duration_of_loop):
             self.logger.info("waiting, time in minutes: %s", i)
             time.sleep(60)
        
        # STEP -------- STEP Check boot message  -------------

        step_description = "Check boot message visible"
        expected_result = "Boot Message Visible"
        actual_result = ""    
        
        t2 = self._get_current_ts_utc()

        boot_message = None
        backend_messages = self.DUT.get_messages(start_time_utc=t1, 
                                                     end_time_utc = t2, 
                                                     max_n_messages=150)
            
        # check the first message sequence 
        for idx, message_ in enumerate(backend_messages):
            if message_["decodedMsg"]["messageType"] == "NBIOT_BOOT":
                boot_message = message_.copy()
                message_2 = backend_messages[idx -1]
                if message_2["decodedMsg"]["messageType"] == "ALPS_STATUS" and message_2["decodedMsg"]["payload"]["alpsMessageType"] == 'STATUS_OTA' and message_2["decodedMsg"]["payload"]["provisionalStatus"] == 'PROVISIONAL':
                    # save time to disocunt it later
                    time_FOTA_provisional =  message_2["decodedMsg"]["header"]["messageGenerationTime"]

                    break

        if boot_message:
            actual_result = "Boot Message Visible"
            step_verdict = self.result_classifier.PASSED
        else:
            actual_result = "No Boot Message Visible" 
            step_verdict = self.result_classifier.FAILED

        self.save_step(7, step_description,
                               expected_result,
                               actual_result,
                               step_verdict)
        

        # STEP -------- Check boot message contents ---------------

        step_description = "Check FW Version (major/minor/sha)"
        expected_result = "Correct FW Loaded"
        actual_result = ""           
        self.logger.info("Step: %s", step_description)
        if (self._check_FW_version_(FW_version_parts, boot_message)):
            actual_result = "Correct FW Loaded: "
            step_verdict = self.result_classifier.PASSED
        else:
            actual_result = "Wrong FW info : "
            step_verdict = self.result_classifier.FAILED
        self.save_step(8, step_description, expected_result, actual_result, step_verdict)


        #  -------- waits to FOTA to be completed, totally 1 hour provisioning time  ---------------

        # Formating time 
        time_now = self._get_current_ts_utc()
        date_format = "%Y-%m-%dT%H:%M:%S"
        time_now = datetime.datetime.strptime(time_now,date_format)
        date_format = "%Y-%m-%dT%H:%M:%S%z"
        time_FOTA_provisional = datetime.datetime.strptime(time_FOTA_provisional,date_format)
        time_FOTA_provisional = time_FOTA_provisional.replace(tzinfo=None)
        time_FOTA_valid_expected = time_FOTA_provisional + datetime.timedelta(hours=1)
             
        pending_time = time_FOTA_valid_expected - time_now 
            
        if pending_time.seconds > 0 :
            minutes_to_wait = int(pending_time.seconds / 60)
            for i in range(minutes_to_wait):
                 self.logger.info("waiting for provisioning time in minutes: remaining time %s", minutes_to_wait - i)
                 time.sleep(60)

        t1 = time_FOTA_provisional
        t2 = time_FOTA_valid_expected
        date_format = "%Y-%m-%dT%H:%M:%S"
        t1 = t1.strftime(date_format)
        t2 = t2.strftime(date_format)
        
    
        backend_messages = self.DUT.get_messages(start_time_utc=t1,
                                                 end_time_utc = t2,
                                                 max_n_messages=150)
        
        
        # STEP -------- validates the sequence of messages for keep alive ----------------- 

        step_description ="Validates the sequence of messages for DL and Keep alive"
        expected_result = "Sequence of messages for DL and Keep alive present and delta time equal to 10 minutes"
        
        list_time_periodic = []
      

        for idx, message_ in enumerate(backend_messages):
            # check for the second message secuence         
            if message_["decodedMsg"]["messageType"] == "ALPS_WIFI_EXTENDED" and message_["decodedMsg"]["state"]  == 'PERIODIC':
                list_time_periodic.append(message_["decodedMsg"]["header"]["messageGenerationTime"])
        
        if not list_time_periodic:
            actual_result = "Sequence of messages not present"
            step_verdict = self.result_classifier.FAILED
        
        # compare times in the array

        for idx, time_ in enumerate(list_time_periodic):
            if ( idx == (len(list_time_periodic) - 1)):
                break
            date_format = "%Y-%m-%dT%H:%M:%S%z"
            time1 = datetime.datetime.strptime(list_time_periodic[idx + 1],date_format)
            time2 = datetime.datetime.strptime(time_,date_format)
            time_delta = time2 - time1
            if (time_delta.seconds == 600):
                step_verdict = self.result_classifier.PASSED
                actual_result = "Sequence of messages for DL and Keep alive present and delta time equal to 10 minutes"
                self.logger.info(" validated time between keep alive euqual to 10 minutes")
            else:
                actual_result = "Sequence of messages present but delta time not equal to 10 minutes"
                step_verdict = self.result_classifier.FAILED

        self.save_step(9, step_description, expected_result, actual_result, step_verdict)



if __name__ == "__main__":
    pass
