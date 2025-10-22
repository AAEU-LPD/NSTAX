"""Interface module to the Qmetry Interface.

This module acts as a bridge between automated testcases already present in Qmetry and
TestSuite executions that are run locally.

Required configuration:
    1. Valid credentials to Qmetry (API Key)
    2. Qmetry test case names to local scripts mapping in the test_config.yaml file with the "qmetry_tag" field
"""

import copy
import json
import time
import requests
import datetime
import xml.etree.ElementTree as ET
from NSTA.testscripts.test_script import ResultClassifier

class QmetryIntegration:
    """Operator class for Qmetry integration to local test results.

        Currently implementated to be triggered from the NSTA framework after tests 
        are complete. This module:

        1. Calls relevant test cases in test host 
        2. Maps test results to the called instances
        3. Uploads the results to the Qmetry test instances

    :param qmetry_url: url of the Qmetry website
    :type qmetry_url: str
    :param automation_api_key: api key for the Automation API
    :type automation_api_key: str
    :param openapi_key: api key for the Open API
    :type openapi_key: str
    :param project_name: name of the project in Qmetry (eg: Hati_System, Lyk_System...)
    :type project_name: str
    :param exec_folder: folder where the test results will be stored
    :type exec_folder: str
    """
    def __init__(self, qmetry_url, automation_api_key, openapi_key, project_name, exec_folder, build_version):
        self.qmetry_url = qmetry_url
        self.project_name = project_name
        self.exec_folder = exec_folder
        self.build_version = build_version
        self.testsuite_id = None
        self.testsuite_run_id = None
        self.testcase_run_id = None
        self.entityKey = None
        self.testcase_step_run_ids = []
        self.qmetry_test_steps = []
        self.qmetry_open_api_headers = {
            'apiKey': openapi_key,
            'project': project_name,
            "Content-Type" : "application/json"
        }
        self.qmetry_automation_api_headers = {
            'apiKey': automation_api_key,
            'project': project_name,
            'Accept':"application/json"
        }
        # Connect to qt server
        self._connect_qmetry_getinfo()
        
    def _connect_qmetry_getinfo(self):
        """Get viewIDs from the Qmetry project to access different elements (Testcases, Testsuites...)
        """
        self.statusIds = {}
        url = f"{self.qmetry_url}/rest/admin/project/getinfo"
        response = requests.get(url=url, headers=self.qmetry_open_api_headers)
        viewIds = json.loads(response.text).get("latestViews")
        statusInfo = json.loads(response.text).get("allstatus")
        builds = json.loads(response.text).get("currentdrops")
        self.TCviewID = viewIds['TC'].get('viewId')
        self.TSviewID = viewIds['TS'].get('viewId')
        self.TEviewID = viewIds['TE'].get('viewId')
        self.TCSviewID = viewIds['TCS'].get('viewId')
        for status in statusInfo:
            status_label = status.get('name')
            rc = ResultClassifier()
                       # Map the status labels to ResultClassifier Class
            if status_label == 'Blocked':
                mapped_status_num = rc.BLOCKED
            elif status_label == 'Failed':
                mapped_status_num = rc.FAILED
            elif status_label == 'Not Run':
                mapped_status_num = rc.NOT_RUN
            elif status_label == 'Passed':
                mapped_status_num = rc.PASSED
            elif status_label == 'Not Applicable':
                mapped_status_num = rc.NO_OP
            else:
                mapped_status_num = rc.NO_OP
            self.statusIds[mapped_status_num] = status.get('id')
        self.dropID = builds[-1].get("DropID")
        for build in builds:
            if build.get("Name") == self.build_version:
                self.dropID = build.get("DropID")
            

    def _get_test_steps(self, automation_content, suite_name):
        """Get the step descriptions or Test Step Summaries from a specified test case

        :param automation_content: contains the test case name (or Testcase summary according to Qmetry)
        :type automation_content: str
        :param suite_name: name of the test suite where the test cases are stored in Qmetry
        :type suite_name: str
        :raises ValueError: error sending REST API request
        :return: returns the entity key assigned to the test case (this is later used for importing results)
        :rtype: str
        """
        # Get Test Case from backend
        request_body = {
            "viewId": self.TCviewID,
            "folderPath": f"/{self.project_name}/{suite_name}"
        }
        url = f"{self.qmetry_url}/rest/testcases/list/viewColumns"
        response = requests.post(url=url, headers=self.qmetry_open_api_headers, json=request_body)
        if not response.ok:
            raise ValueError("Error in Post command !", response.status_code, response.reason, response.content)
        for test_case in json.loads(response.text).get("data"):
            if test_case["name"] == automation_content:
                # tcFolderId = test_case["tcFolderId"]
                version = test_case["associatedVersion"]
                tcId = test_case["id"]
                entityKey = test_case['entityKey']
        # Get Test Case Steps from backend
        request_body = {
            "id": tcId,
            "start": 0,
            "page": 1,
            "limit": 50,
            "version": version,
        }
        url = f"{self.qmetry_url}/rest/testcases/steps/list"
        response = requests.post(url=url, headers=self.qmetry_open_api_headers, json=request_body)
        if not response.ok:
            raise ValueError("Error in Post command !", response.status_code, response.reason, response.content)
        qmetry_steps = []
        for test_step in json.loads(response.text).get("data"):
            temp_step = {}
            temp_step["description"] = test_step["description"]
            # temp_step["expectedOutcome"] = test_step["expectedOutcome"]
            qmetry_steps.append(temp_step)
        self.qmetry_test_steps = copy.deepcopy(qmetry_steps)
        return entityKey
    
    def _generate_robot_xml(self, test_suite, suite_name):
        """Generate an xml format ROBOT file and return in bytes format

        :param test_suite: array of testcase dicts that stores result information
        :type test_suite: list
        :param suite_name: name of the test suite where the test cases are stored in Qmetry
        :type suite_name: str
        :return: the xml doc formatted as bytes
        :rtype: str (bytes)
        """
        # Create XML elements
        root = ET.Element("robot", generated=datetime.datetime.now().isoformat(), generator="NSTA Framework")
        suite = ET.SubElement(root, "suite", name=suite_name, source="placeholder.robot")
        for test_case in test_suite:
            result_steps = test_case["result_steps_"]
            result_overall = test_case["result_overall_"]
            automation_content = test_case["automation_content_"]
            test_case["entity_key"] = self._get_test_steps(automation_content, suite_name)
            test = ET.SubElement(suite, "test", name=automation_content)
            # Assign overall result string
            result_classifier = ResultClassifier()
            if result_overall == result_classifier.PASSED:
                final_status = "PASS"
            elif result_overall == result_classifier.FAILED:
                final_status = "FAIL"
            else:
                final_status = "SKIP"
            for index, result_step in result_steps.items():
                description = self.qmetry_test_steps[index - 1]["description"]
                step_status = ""
                # Fill result from local run
                if result_step["verdict"] == result_classifier.PASSED:
                    step_status = "PASS"
                elif result_step["verdict"] == result_classifier.FAILED:
                    step_status = "FAIL"
                else:
                    step_status = "SKIP"
                kw = ET.SubElement(test, "kw", name=f"{description}")
                ### TODO: implement actual start/end times (Currently placeholder times required for uploading)
                start_time = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
                end_time = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
                ###
                status = ET.SubElement(kw, "status", status=step_status, starttime=start_time, endtime=end_time)
            status_test = ET.SubElement(test, "status", status=final_status, starttime=start_time, endtime=end_time)
        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        return xml_bytes
    
    def _update_actual_result(self, local_test_suite, testSuiteId):
        """Update the actualResult fields in the test execution in Qmetry

        :param local_test_suite: the local test case suite that contains the result information
        :type local_test_suite: list
        :param testSuiteId: ID of the execution test suite in Qmetry
        :type testSuiteId: int
        :raises ValueError: error in sending REST API request
        """
        # Get all test suites
        request_body = {
            "viewId": self.TSviewID,
            "folderPath": f"/{self.project_name}/{self.exec_folder}"
        }
        url = f"{self.qmetry_url}/rest/testsuites/list/viewColumns"
        response = requests.post(url=url, headers=self.qmetry_open_api_headers, json=request_body)
        if not response.ok:
            raise ValueError("Error in Post command !", response.status_code, response.reason, response.content)
        for stored_test_suites in json.loads(response.text).get("data"):
            tsID = stored_test_suites.get("id")
            if tsID == testSuiteId:
                # Get associated test execution with the suite
                subrequest_body = {
                    "tsID": tsID
                }
                url = f"{self.qmetry_url}/rest/execution/list/platformHome"
                subresponse = requests.post(url=url, headers=self.qmetry_open_api_headers, json=subrequest_body)
                if not subresponse.ok:
                    raise ValueError("Error in Post command !", subresponse.status_code, subresponse.reason, subresponse.content)
                tsRunID = json.loads(subresponse.text).get("data")[0].get("tsRunID")
                # Get associated test case
                subrequest_body = {
                    "viewId": self.TCviewID,
                    "tsrunID": tsRunID,
                }
                url = f"{self.qmetry_url}/rest/execution/list/viewColumns"
                subresponse = requests.post(url=url, headers=self.qmetry_open_api_headers, json=subrequest_body)
                if not subresponse.ok:
                    raise ValueError("Error in Post command !", subresponse.status_code, subresponse.reason, subresponse.content)
                for qmetry_test_case in json.loads(subresponse.text).get("data"):
                    entityKey = qmetry_test_case.get("entityKey")
                    qmTsRunId = qmetry_test_case.get("tsRunID")
                    tcrID = qmetry_test_case.get("tcRunID")
                    for local_test_case in local_test_suite:
                        if entityKey == local_test_case["entity_key"]:
                            result_steps = local_test_case["result_steps_"]
                            result_overall = local_test_case["result_overall_"]
                    # Get associated test steps
                    subrequest_body = {
                        "viewId": self.TCSviewID,
                        "tcrID": tcrID,
                        "scope": "cycle",
                    }
                    url = f"{self.qmetry_url}/rest/execution/tcStepRun/list/viewColumns"
                    subresponse = requests.post(url=url, headers=self.qmetry_open_api_headers, json=subrequest_body)
                    if not subresponse.ok:
                        raise ValueError("Error in Post command !", subresponse.status_code, subresponse.reason, subresponse.content)
                    for test_step in json.loads(subresponse.text).get("data"):
                        # Update the actualResult information for each step
                        tcStepRunID = test_step.get("tcStepRunID")
                        qmTsRunId = test_step.get("tsRunID")
                        stepNo = test_step.get("stepNo")
                        subreq_body = {
                            "entityId": tcStepRunID,
                            "field": "actualResult",
                            "fieldVal": result_steps[stepNo]["actual_result"],
                            "type": "TCSR"
                        }
                        url = f"{self.qmetry_url}/rest/execution/updaterun"
                        subresponse = requests.put(url=url, headers=self.qmetry_open_api_headers, json=subreq_body)
                        if not subresponse.ok:
                            raise ValueError("Error in Put command !", subresponse.status_code, subresponse.reason, subresponse.content)
                        # Update the runStatus for each step
                        subreq_body = {
                            "entityIDs": f"{tcStepRunID}",
                            "qmTsRunId": qmTsRunId,
                            "runStatusID": self.statusIds[result_steps[stepNo]["verdict"]],
                            "dropID": self.dropID,
                            "entityType": "TCSR"
                        }
                        url = f"{self.qmetry_url}/rest/execution/runstatus/bulkupdate"
                        subresponse = requests.put(url=url, headers=self.qmetry_open_api_headers, json=subreq_body)
                        if not subresponse.ok:
                            raise ValueError("Error in Put command !", subresponse.status_code, subresponse.reason, subresponse.content)
                    # Update the runStatus for each test case
                    subreq_body = {
                        "entityIDs": f"{tcrID}",
                        "qmTsRunId": qmTsRunId,
                        "runStatusID": self.statusIds[result_overall],
                        "dropID": self.dropID,
                        "entityType": "TCR"
                    }
                    url = f"{self.qmetry_url}/rest/execution/runstatus/bulkupdate"
                    subresponse = requests.put(url=url, headers=self.qmetry_open_api_headers, json=subreq_body)
                    if not subresponse.ok:
                        raise ValueError("Error in Put command !", subresponse.status_code, subresponse.reason, subresponse.content)
                           
    def post_test_result(self, test_suite_, suite_name_, post_actual_result=True):
        """POST test result to Qmetry.
        
        :param test_suite_: array of testcase dicts that stores result information
        :type test_suite_: list
        :param suite_name_: name of the test suite where the test cases are stored in Qmetry
        :type suite_name_: str
        :param post_actual_result: whether to update the actualResult fields in the test execution, defaults to True
        :type post_actual_result: bool, optional
        :raises ValueError: error in sending REST API request
        """
        xml_bytes = self._generate_robot_xml(test_suite_, suite_name_,)
        # Get Test Case from backend
        request_body = {
            "entityType": (None, "ROBOT"),
            "file": ("file.xml", xml_bytes, "application/xml"),
            "tsFolderPath": (None, self.exec_folder),
            "is_matching_required": (None, "false")
        }
        url = f"{self.qmetry_url}/rest/import/createandscheduletestresults/1"
        response = requests.post(url=url, headers=self.qmetry_automation_api_headers, files=request_body)
        if not response.ok:
            raise ValueError("Error in Post command !", response.status_code, response.reason, response.content)
        if post_actual_result:
            # Update the actualResult fields in the test execution
            time.sleep(2)
            requestId = json.loads(response.content.decode('utf-8'))["requestId"]
            url = f"{self.qmetry_url}/rest/admin/status/automation/{requestId}"
            response = requests.get(url=url, headers=self.qmetry_automation_api_headers)
            if not response.ok:
                raise ValueError("Error in Get command !", response.status_code, response.reason, response.content)
            testSuiteId = json.loads(response.content.decode('utf-8'))["testSuiteData"][0]["testSuiteId"]
            self._update_actual_result(test_suite_, testSuiteId)
            

if __name__ == "__main__":
    QM = QmetryIntegration("https://testmanagementeu.qmetry.com", "1nykrkWODm6mFNfH4vTw44Xdv4OCBNbJCp19R16U", "zK2zajc7YVAcazpQVIiLF8UO15o715uzp1SPEXyo", "Hati_System", "HATI_TEST")
    test_suite_ = []
    result_overall_ = 2
    suite_name_ = "Device_Connectivity"
    automation_content_ = "[Automated] Cell ID Cell Attach"
    start_time_ = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
    end_time_ = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
    result_steps_ = {
        1: {'verdict': 1, 'actual_result': 'Setup successful. Starting Test.'},
        2: {'verdict': 2, 'actual_result': 'Received location message successfully.'},
        3: {'verdict': 4, 'actual_result': 'Cell ID (27447560) is valid Attach: TEST'},
    }
    test_case = {
        "start_time_": start_time_,
        "result_steps_": result_steps_,
        "result_overall_": result_overall_,
        "automation_content_": automation_content_,
        "end_time_": end_time_
    }
    test_suite_.append(test_case)
    result_overall_ = 4
    automation_content_ = "[Automated] Cell ID Cell Attach TRUMI"
    start_time_ = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
    end_time_ = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
    result_steps_ = {
        1: {'verdict': 2, 'actual_result': 'Setup successful. Starting Test.'},
        2: {'verdict': 2, 'actual_result': 'Received location message successfully.'},
        3: {'verdict': 2, 'actual_result': 'Cell ID (27447560) is valid Attach: TEST'},
    }
    test_case = {
        "start_time_": start_time_,
        "result_steps_": result_steps_,
        "result_overall_": result_overall_,
        "automation_content_": automation_content_,
        "end_time_": end_time_
    }
    test_suite_.append(test_case)
    QM.post_test_result(test_suite_, suite_name_)
