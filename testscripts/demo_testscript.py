"""Demo test scripts."""


from NSTAX.testscripts.test_script import TestScript


class SFULMessageCheck(TestScript):
    """Check NbIoT UL Messages.

    This testcase compares UL messages (as pre-defined in ul_messages_raw) with
    the messages actually sent by a tracker with a special FW.

    Check is a simple string comparison between the RAW messages only.

    Whole purpose of this test is to check if the UL messages are properly
    passed to the backend in the right order without losing any content.
    """
    def __init__(self):
        super().__init__()
        self.name = "NBIOTULMessageCheck"
        self.automation_content = "LYKN5_NBIOT_UL_RAW_MessageCheck"
        self.version = 0.1
        self.requirement["DUT"].append("PlatformDevice")
        self.ul_messages_raw = (
            "c87d",                     # activation message
            "f04100",                   # downlink ACK
            "e8000e0e00007d",           # downlink request
            "c07d00",                   # normal message
            "c17d26",                   # transit message
            "e906000090000f4a120046",   # trumi alarm message
            "e90000325a0008f4070200",   # orientation status message
            "d9235fa0a018339cd00057",   # diagnostic message
            "d8214fee12002732ca0010",   # periodic diagnostic message
            "122456a1002102abcd479c05", # normal message
            "122456a1002103abcd479c05", # keep alive message
            "3b2456a1002103abcd479c05", # DI keep alive message
            "3b2456a1002102abcd479c05", # DI normal message
            "f87a",                     # DI status message
        )
        self.n_steps = 1 + len(self.ul_messages_raw)

    def teststeps(self):
        # Step 1: Activate/Flash/RESET_IC the device
        self.save_step(1, self.result_classifier.PASSED, "Device activated")
        self.logger.info("Device activated")
        backend_messages_t = self.DUT.get_messages(start_time_utc="2022-09-21T14:00:00", end_time_utc = "2022-09-21T15:00:00", max_n_messages=50)
        backend_messages = []
        for message_ in backend_messages_t:
            if message_["decodedMsg"]["messageType"] not in ("NBIOT_DIAGNOSTICS", "NBIOT_BOOT",):
                backend_messages.append(message_["rawMsg"]["dataDecoded"])
        backend_messages = list(reversed(backend_messages))
        if len(backend_messages) != len(self.ul_messages_raw):
            test_step_ctr = 1
            for expected_message in self.ul_messages_raw:
                test_step_ctr += 1
                backend_message = backend_messages[test_step_ctr - 2]
                Pass = expected_message == backend_message
                if Pass:
                    self.save_step(test_step_ctr, self.result_classifier.PASSED, f"Message matched ({backend_message})")
                    self.logger.info("Message matched !")
                else:
                    self.save_step(test_step_ctr, self.result_classifier.FAILED, f"Message did not match ({backend_message}) ")
                    self.logger.info("Message did not match !")
        else:
            self.logger.error("None or bad number of messages received from the backend !")
            self.logger.info("Backend Messages: %s" %backend_messages)


class PSSMessageFlow(TestScript):
    """Check the PSS message content of Lykaner"""
    def __init__(self):
        super().__init__()
        self.name = "PSSMessageFlow"
        self.automation_content = "LYK_PSSMessageFlow"
        self.version = 0.1
        self.requirement["DUT"].append("Sigfox")
        self.n_steps = 4

    def lyk_find_message_type(self, message):
        """Returns known message types"""
        message_type = "others"
        if len(message) == 24:
            type_00 = int(message[2], 16) & 1
            type_60 = int(message[13], 16) & 1
            if type_00 == 0:
                if type_60 == 0:
                    message_type = "NORMAL_DATA_WIFI"
                else:
                    message_type = "KEEPALIVE_DATA_WIFI"
            else:
                if type_60 == 0:
                    message_type = "NORMAL_DATA_WIFI_DI"
                else:
                    message_type = "KEEPALIVE_DATA_WIFI_DI"
        elif len(message) == 8:
            message_byte_1 = format(int(message[0:2], 16), "08b")
            message_type_t = int(message_byte_1[-1] + message_byte_1[2:5], 2)
            if message_type_t == 13:
                message_type = "FUNCTION_SPECIFIC"
                message_byte_2 = message_byte_1 = format(int(message[2:4], 16), "08b")
                message_sub_frame_id = int(message_byte_2[0:2], 2)
                message_specific_function_id = int(message_byte_2[2:9], 2)
                if message_specific_function_id == 3 and message_sub_frame_id == 1:
                    message_type = "FUCNTION_SPECIFIC_PERIODIC_SEND"
        return message_type

    def teststeps(self):
        """Test steps."""
        # Step 1: Activate the device
        self.save_step(1, self.result_classifier.PASSED, "Device activated")
        self.logger.info("Device activated")
        # Step 2: Wait 12 Hours
        self.save_step(2, self.result_classifier.PASSED, "Wait 12 hours")
        self.logger.info("Wait 12 hours")
        # Step 3: Check for WiFi messages
        messages = self.DUT.get_messages(limit=100, since="2022-09-08 03:46:46", before="2022-09-10 23:59:59")
        error_message = ""
        try:
            message_1 = messages[-1]["data"]
        except IndexError:
            message_1 = {}
            error_message = "No WiFi message is found!"
        message_type = self.lyk_find_message_type(message_1)
        if message_type == "KEEPALIVE_DATA_WIFI":
            self.save_step(3, self.result_classifier.PASSED, "WiFi message found")
            self.logger.info("WiFi message found")
        else:
            error_message = "No WiFi message is found!"
        if error_message:
            self.save_step(3, self.result_classifier.FAILED, error_message)
            self.logger.info(error_message)
        # Step 4: Check for PSS messages
        error_message = ""
        try:
            message_2 = messages[-2]["data"]
        except IndexError:
            message_2 = {}
            error_message = "No PSS message is found!"
        message_type = self.lyk_find_message_type(message_2)
        if message_type == "FUCNTION_SPECIFIC_PERIODIC_SEND":
            self.save_step(4, self.result_classifier.PASSED, "PSS message found")
            self.logger.info("PSS message found")
        else:
            error_message = "No PSS message is found!"
        if error_message:
            self.save_step(4, self.result_classifier.FAILED, error_message)
            self.logger.info(error_message)


if __name__ == "__main__":
    pass
