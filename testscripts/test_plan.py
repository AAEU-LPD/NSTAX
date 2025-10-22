""" Test entities for all test cases.
"""


class TestSuite:
    """Represents a test suite."""
    def __init__(self, suite_name, build_version=None, suite_tag=None):
        self.suite_name = suite_name
        self.test_instances = []
        self.test_cases = []
        self.suite_tag = suite_tag
        self.build_version = build_version
        self.number_of_test_instances = 0

    def append_test_instance(self, test_instance):
        """Appends a test instance to the suite.

        :param test_instance: Test instance to append
        :type test_instance: TestInstance
        """
        self.test_instances.append(test_instance)
        self.number_of_test_instances += 1


class TestInstance:
    """Represents a test instance."""
    def __init__(self, device_instance_dict, test_script_name, params_from_testcfg):
        self.device_instance_dict = device_instance_dict
        self.test_script_name = test_script_name
        self.params_from_testcfg = params_from_testcfg
        self.TS = None
        self.test_result = TestResult()


class TestResult:
    """Represents a test result."""
    def __init__(self):
        self.result = 0
        self.result_per_step = {}
        self.result_output = {}


if __name__ == "__main__":
    pass
