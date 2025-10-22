"""Interface module to the Tricentis qTest.

This module acts as a bridge between automated testcases in Tricentis qTest and
standalone test scripts run locally.

Required configuration:
    1. Valid credentials to qTest
    2. qTest test case names to local script mapping
"""


import json
import base64
import time
import copy
from datetime import datetime
import requests
from NSTA.testscripts.test_script import ResultClassifier


class QTestIntegration:
    """ Operator class for qTest integration to local test results.

        Ideally to be called from qTest Automation Host with test input
        parameters. This module:

        1. Calls relevant test cases in test host
        2. Maps test results to the called instances
        3. Uploads the results to the qTest test instances

        :param qtest_url: URL of qTest server
        :type qtest_url: str
        :param username: qTest username
        :type username: str
        :param password: qTest password
        :type password: str
        :param project_id: Project ID of the relevant test suite
        :type project_id: int
        :param testcycle_name: Test cycle ID
        :type testcycle_name: int
    """
    def __init__(self, qtest_url, username, password, project_id, testcycle_name):
        self.qt_url = qtest_url
        self.username = username
        self.password = password
        self.qt_project_id = project_id
        self.testcycle_name = testcycle_name
        self.testcase_id = None
        self.testrun_id = None
        self.qt_test_steps = []
        self.qt_headers = {
            "Content-Type" : "application/json",
        }
        # Connect to qt server
        self._connect_qt_server()

    def _connect_qt_server(self):
        """ Connect to qTest server with given credentials
        """
        url = self.qt_url + "/oauth/token"
        to_encode = self.username + ':'
        auth = "Basic " + (base64.b64encode(to_encode.encode('utf-8')).decode('utf-8'))
        auth_headers = {
            "Content-Type" : "application/x-www-form-urlencoded",
            "Authorization" : auth
        }
        body = {
            "grant_type" : "password",
            "username" : self.username,
            "password" : self.password
        }
        t_response = requests.post(url = url, headers = auth_headers, data = body)
        if t_response.ok:
            response = json.loads(t_response.content)
            token = "bearer " + response['access_token']
            self.qt_headers['Authorization'] = token
            # return token
        else:
            t_response.raise_for_status()

    def _get_test_ids(self, automation_content):
        body = {
            "object_type": "test-runs",
            "fields": ["*",],
            "query": f"'Test Case Automation Content' = '{automation_content}' and 'Test Cycle' = '{self.testcycle_name}'"
        }
        url = f"{self.qt_url}/api/v3/projects/{self.qt_project_id}/search".format(self.qt_url, self.qt_project_id)
        response_ = requests.post(url = url, headers = self.qt_headers, data = json.dumps(body))
        if response_.ok:
            response = json.loads(response_.content)
        else:
            response_.raise_for_status()

        if len(response.get("items")) != 1:
            raise ValueError("# None or multiple test runs found")
        try:
            self.testrun_id = int(response["items"][0]["id"])
            self.testcase_id = int(response["items"][0]["testCaseId"])
            return True
        except (KeyError, IndexError, ValueError) as e_:
            return False

    def _get_test_steps(self):
        qt_steps = []
        url = f"{self.qt_url}/api/v3/projects/{self.qt_project_id}/test-cases/{self.testcase_id}"
        response = requests.get(url=url, headers=self.qt_headers, params={})
        if not response.ok:
            raise ValueError("Error in Get command !", response.status_code, response.reason, response.content)
        for test_step in json.loads(response.text).get("test_steps"):
            temp_step = {}
            temp_step["description"] = test_step["description"]
            temp_step["expected"] = test_step["expected"]
            qt_steps.append(temp_step)
        self.qt_test_steps = copy.deepcopy(qt_steps)

    def qt_write_test_log(self, result_steps, result_overall, automation_content):
        """Write results to qTest

        :param result_steps: Test result on each step
        :type result_steps: dict
        :param result_overall: Combined / Final test result
        :type result_overall: int
        :param automation_content: Unique qTest automation content to map test cases
        :type automation_content: str
        """
        if not self._get_test_ids(automation_content):
            raise ValueError("No test case/run found withe the given query")
        self._get_test_steps()
        test_steps_to_upload = []
        start_time = datetime.now().isoformat()[:-3] + "Z"
        # TODO: Port actual test starting time
        time.sleep(1)
        end_time = datetime.now().isoformat()[:-3] + "Z"
        # TODO: Port actual test ending time
        # Overall result
        result_classifier = ResultClassifier()
        if result_overall == result_classifier.PASSED:
            final_result = "PASS"
        elif result_overall == result_classifier.FAILED:
            final_result = "FAIL"
        else:
            final_result = "SKIP"
        for index, result_step in result_steps.items():
            test_step_to_upload = {}
            # Fill result from local run
            if result_step["verdict"] == result_classifier.PASSED:
                test_step_to_upload["status"] = "PASS"
            elif result_step["verdict"] == result_classifier.FAILED:
                test_step_to_upload["status"] = "FAIL"
            else:
                test_step_to_upload["status"] = "SKIP"
            test_step_to_upload["order"] = index
            test_step_to_upload["actual_result"] = result_step["actual_result"]                 # Fill from local result
            test_step_to_upload["description"] = self.qt_test_steps[index - 1]["description"]   # Fill from qTest content
            test_step_to_upload["expected_result"] = self.qt_test_steps[index - 1]["expected"]  # Fill from qTest content
            test_steps_to_upload.append(copy.deepcopy(test_step_to_upload))
            # TODO: Add more fields, attachments, ...
        body = {
            "status" : final_result,
            "exe_start_date" : start_time,
            "exe_end_date" : end_time,
            "automation_content" : automation_content,
            "test_step_logs": test_steps_to_upload
        }
        url = f"{self.qt_url}/api/v3/projects/{self.qt_project_id}/test-runs/{self.testrun_id}/auto-test-logs"
        r = requests.post(url = url, headers = self.qt_headers, data = json.dumps(body))
        if r.ok:
            response = json.loads(r.content)
        else:
            r.raise_for_status()


if __name__ == "__main__":
    QT = QTestIntegration("https://alpsalpine.qtestnet.com", "debasish.chanda@alpsalpine.com", "_PASSWORD_", 107344, 4367028)
    result_overall_ = 2
    result_steps_ = {
        1: {'verdict': 1, 'actual_result': 'Device activated'},
        2: {'verdict': 2, 'actual_result': 'Wait 12 hours'},
        3: {'verdict': 2, 'actual_result': 'WiFi message found'},
        4: {'verdict': 2, 'actual_result': 'PSS message found'}
    }
    QT.qt_write_test_log(result_steps_, result_overall_, "LYK_PSSMessageFlow")
