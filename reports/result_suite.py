"""Test result structure for generic reporting.

This module defines the pythonic test result data structure as the baseline for
needed reporting modules.
"""

import copy
import json

from NSTAX.testscripts.test_script import ResultClassifier


class ResultSuite:
    """Pythonic result structure generator class.

        :param test_suite: Test result instance
        :type test_suite: TestSuite
    """
    def __init__(self, test_suite):
        self.test_suite_input = test_suite
        self.test_suite = {}
        self.test_suite["test_instances"] = []
        self._init_test_suite()

    def _init_test_suite(self):
        self.test_suite["name"] = self.test_suite_input.suite_name
        tmp_classifier = ResultClassifier()
        for test_instance in self.test_suite_input.test_instances:
            ti_tmp = {}
            ti_tmp["name"] = test_instance.TS.name
            ti_tmp["version"] = test_instance.TS.version
            ti_tmp["description"] = test_instance.TS.description
            ti_tmp["dut_info"] = test_instance.device_instance_dict.copy()
            ti_tmp["result"] = tmp_classifier.get_result_string(test_instance.test_result.result)
            ti_tmp["result_step"] = copy.deepcopy(test_instance.test_result.result_per_step)
            ti_tmp["result_output"] = copy.deepcopy(test_instance.test_result.result_output)
            for index_, result_ in ti_tmp["result_step"].items():
                # Convert per step results classifiers to text
                result_["verdict"] = tmp_classifier.get_result_string(result_["verdict"])
            self.test_suite["test_instances"].append(copy.deepcopy(ti_tmp))

    def get_raw_result(self):
        """Returns result structure.

        :return: Pythonic result structure
        :rtype: dict
        """
        return self.test_suite

    def get_json_result(self, pretty=False):
        """Returns result structure in json format.

        :param pretty: pretty formatting enabled, default: False
        :type pretty: bool, optional

        :return: Result structure in json
        :rtype: str
        """
        if pretty:
            return json.dumps(self.test_suite, sort_keys=True, indent=2)
        else:
            return json.dumps(self.test_suite)
