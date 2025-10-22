"""Dummy test script module for framework check."""


from NSTA.testscripts.test_script import TestScript


class DummyTestScript(TestScript):
    """Dummy Test"""
    def __init__(self):
        super().__init__()
        self.name = "DummyTest"
        self.version = 0.1
        self.requirement["DUT"].append("DummyDevice")

    def teststeps(self):
        """Test steps."""
        # Step 1
        self.save_step(1, self.result_classifier.PASSED, "Step 1: Step one completed")
        self.logger.info("Step 1: Step one completed")

        # Step 2
        self.save_step(4, self.result_classifier.PASSED, "Step 2: Write xxx to the dummy device")
        self.DUT.send_debug_command("xxx")
        self.logger.info("Step 2: Write xxx to the dummy device")

        # Step 3: Read from the dummy device
        data = self.DUT.receive_debug_readout()
        # Check data validity (pass condition)
        if data == "xxx":
            result_step = self.result_classifier.PASSED
        else:
            result_step = self.result_classifier.FAILED
        self.save_step(3, result_step, "Step 3: Step three completed")
        self.logger.info("Step 3: Step three completed")
