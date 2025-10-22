"""Main TA controller module."""


import os
import logging
import datetime
import importlib
import yaml

from NSTAX.devices.dummy_device import *
from NSTAX.devices.sigfox_device import *
from NSTAX.devices.platform_device import *
from NSTAX.equipment.NSTA25M import *
from NSTAX.equipment.NSTA25MV import *
from NSTAX.equipment.NSTA25V import *
from NSTAX.equipment.IKAHS501 import *
from NSTAX.equipment.IKAKS130 import *
from NSTAX.equipment.AMARISOFT import *
from NSTAX.equipment.XARM import *
from NSTAX.equipment.SHKR2075E import *
from NSTAX.equipment.DT9837 import *
from NSTAX.testscripts import *
from NSTAX.testscripts.test_plan import TestSuite, TestInstance
from NSTAX.reports.result_suite import ResultSuite
from NSTAX.reports.report_engine import ReportEngine
from NSTAX.QT.QTestIntegration import QTestIntegration
from NSTAX.Qmetry.QmetryIntegration import QmetryIntegration
import NSTA


class TestRun:
    """Test run engine."""

    def __init__(self):
        self.teststation_config_file = "./config/teststation_config.yaml"
        self.test_config_file = "./config/test_config.yaml"
        self.autolog_file = "autolog.txt"
        self.report_template_directory = "./reports/"
        self.report_template_filename = "report_template.html"
        self.html_report_filename = "result.html"
        self.teststation_config = {}
        self.log_folder = "./"  # Runtime update occurs later
        self.test_config = {}
        self.qt_integration = False
        self.qt_url = ""
        self.qt_username = ""
        self.qt_password = ""
        self.qt_project_id = 0
        self.qt_testcycle_id = 0
        self.qmetry_integration = False
        self.qmetry_url = ""
        self.qmetry_automation_api_key = ""
        self.qmetry_openapi_key = ""
        self.qmetry_project_name = ""
        self.qmetry_exec_folder = ""
        self.test_suite = None
        self.logger = logging.getLogger('NSTA.{}'.format(__name__))

    def initialize(self):
        """Inititlize the system test parameters."""
        # Initialize logger
        self._init_logger()
        # Read config
        self._read_config()
        # Initialize data loggers
        self._init_data_loggers()
        # Check qTest configuration
        self._read_qtest_config()
        # Check Qmetry configuration
        self._read_qmetry_config()
        # Create a tests-to-run list
        self._create_test_instances()

    def setup(self, TS):
        """Connect to the DUT and EQUIPMENT."""
        if TS.DUT:
            if isinstance(TS.DUT, list):
                for dut in TS.DUT:
                    dut.connect()
            else:
                TS.DUT.connect()
        if TS.EQUIPMENT:
            if isinstance(TS.EQUIPMENT, list):
                for equ in TS.EQUIPMENT:
                    equ.connect()
            else:
                TS.EQUIPMENT.connect()
        # Connect Data Loggers
        if self.data_loggers:
            for d_logger in self.data_loggers:
                path = f"{TS.log_folder}\\datalogs_{TS.name}"
                # Create result folder
                if not os.path.exists(path):
                    os.makedirs(path)
                d_logger.connect(path)

    def teardown(self, TS):
        """Teardown the system test parameters."""
        if TS.DUT:
            if isinstance(TS.DUT, list):
                for dut in TS.DUT:
                    dut.disconnect()
            else:
                TS.DUT.disconnect()
        if TS.EQUIPMENT:
            if isinstance(TS.EQUIPMENT, list):
                for equ in TS.EQUIPMENT:
                    equ.disconnect()
            else:
                TS.EQUIPMENT.disconnect()
        # Disconnect Data Loggers
        if self.data_loggers:
            for d_logger in self.data_loggers:
                d_logger.disconnect()

    def _init_logger(self):
        """Initialize autolog."""
        result_foldername = "test_{}".format(datetime.now().strftime('%Y%m%d_%H%M%S'))
        self.log_folder = os.path.join(os.path.dirname(NSTA.__file__), "results", result_foldername)
        # Create result folder
        if not os.path.exists(self.log_folder):
            os.makedirs(self.log_folder)
        # Create autologger
        autolog_abs_path = os.path.join(self.log_folder, self.autolog_file)
        self.logger = logging.getLogger("NSTA")
        self.logger.setLevel(logging.INFO)
        logfile_handler = logging.FileHandler(autolog_abs_path)
        formatter = logging.Formatter("%(asctime)s|%(name)s|%(levelname)s|%(message)s")
        logfile_handler.setFormatter(formatter)
        self.logger.addHandler(logfile_handler)
        self.logger.info("Created auto logger: %s", autolog_abs_path)

    def _read_config(self):
        """Read cofiguration fies."""
        # Read teststation config
        self.logger.info("Reading teststation config from file: %s", self.teststation_config_file)
        with open(self.teststation_config_file, 'r') as data_stream:
            try:
                self.teststation_config.update(yaml.safe_load(data_stream))
            except yaml.YAMLError as error_:
                print(error_)
        self.logger.info("Teststation config: %s", self.teststation_config)
        # Read test config
        self.logger.info("Reading tests config from file: %s", self.test_config_file)
        with open(self.test_config_file, 'r') as data_stream:
            try:
                self.test_config.update(yaml.safe_load(data_stream))
            except yaml.YAMLError as error_:
                print(error_)
        self.logger.info("Test config: %s", self.test_config)

    def _init_data_loggers(self):
        self.data_loggers = []
        dut_list = self.teststation_config["device"]
        for dut in dut_list:
            device_name = dut["name"]
            device_parameters = dut.get("parameters")
            if device_parameters:
                logger_params = device_parameters.get("logger_params")
                if logger_params:
                    is_logging_enabled = logger_params.get("data_logging_en")
                    if is_logging_enabled:
                        logger_port = logger_params["log_port"]
                        logger_timestamps_en = logger_params["log_timestamps"]
                        device_logger = Logger(device_name, logger_port, logger_timestamps_en)
                        self.data_loggers.append(device_logger)
                        self.logger.info(f"DATA LOGGING ENABLED for: {device_name}")
                        # TODO: remove elses?
                    else:
                        self.logger.info(f"DATA LOGGING DISABLED for: {device_name}")
                else:
                    self.logger.info(f"LOGGER CONFIG NOT FOUND for: {device_name}")
            else:
                self.logger.info(f"NO DEVICE CONFIG FOUND for: {device_name}")

    def _read_qtest_config(self):
        """Gather qtest configuration"""
        qtest_parameters = self.teststation_config.get("qtest")
        if qtest_parameters:
            self.qt_integration = qtest_parameters["enabled"]  # check type
            self.qt_url = qtest_parameters["url"]
            self.qt_username = qtest_parameters["username"]
            self.qt_password = qtest_parameters["password"]
            self.qt_project_id = qtest_parameters["project_id"]
            self.qt_testcycle_id = qtest_parameters["testcycle_id"]

    def _read_qmetry_config(self):
        """Gather qmetry configuration"""
        qmetry_parameters = self.teststation_config.get("qmetry")
        if qmetry_parameters:
            self.qmetry_integration = qmetry_parameters["enabled"]  # check type
            self.qmetry_url = qmetry_parameters["url"]
            self.qmetry_automation_api_key = qmetry_parameters["automation_api_key"]
            self.qmetry_openapi_key = qmetry_parameters["openapi_key"]
            self.qmetry_project_name = qmetry_parameters["project_name"]
            self.qmetry_exec_folder = qmetry_parameters["exec_folder"]

    def _create_test_instances(self):
        """Create test instances."""
        device_instance_dict = []
        self.logger.info("Creating test instances")
        test_suite = self.test_config["testsuite"][0]  # TODO: multiple test suite support
        test_suite_name = test_suite["name"]
        build_version = test_suite.get("build_version", None)
        suite_tag = test_suite.get("qmetry_tag", None)
        if self.qmetry_integration:
            if build_version is None or suite_tag is None:
                raise ValueError("Missing Qmetry Parameters")
        self.test_suite = TestSuite(test_suite_name, build_version, suite_tag)
        for test_instance_t in test_suite["tests"]:
            test_script_name = test_instance_t["name"]
            dut_index = test_instance_t["dut_index"]
            params_from_testcfg = test_instance_t.get("test_parameters", {})
            if isinstance(dut_index, list):
                for d_idx in dut_index:
                    # if its already a dict. Make it a array.
                    if device_instance_dict and isinstance(device_instance_dict, dict):
                        device_instance_dict = [device_instance_dict]

                    device_obj = self.teststation_config["device"][d_idx]
                    if device_obj not in device_instance_dict:
                        device_instance_dict.append(device_obj)
            else:
                device_obj = self.teststation_config["device"][dut_index]
                # if its already an array.
                if device_instance_dict and isinstance(device_instance_dict, list):
                    if device_obj not in device_instance_dict:
                        device_instance_dict.append(device_obj)
                else:
                    device_instance_dict = device_obj
            test_instance_t = TestInstance(device_instance_dict, test_script_name, params_from_testcfg)
            self.test_suite.append_test_instance(test_instance_t)

    def _create_dependencies(self):
        test_suite_module = importlib.import_module("NSTA.testscripts.{}".format(self.test_suite.suite_name))
        for test_instance_t in self.test_suite.test_instances:
            # Create test script
            test_script_obj = eval("test_suite_module.{}".format(test_instance_t.test_script_name))
            TS = test_script_obj()
            # Check script version
            if TS.version == 0.0:
                raise ValueError("Check Script Version")

            # Create script DUT dependency
            if TS.requirement["DUT"]:
                if isinstance(test_instance_t.device_instance_dict, list):
                    TS.DUT = []
                    # Create multiple DUT instances
                    for device_instance in test_instance_t.device_instance_dict:
                        device_type_obj = eval(device_instance["type"])
                        device_name = device_instance["name"]
                        device_parameters = device_instance.get("parameters")
                        if device_parameters:
                            device_object = device_type_obj(device_name, **device_parameters)
                        else:
                            device_object = device_type_obj(device_name)
                        TS.DUT.append(device_object)
                        device_type = device_object.type
                        if device_type not in TS.requirement["DUT"]:
                            raise ValueError("Check DUT Requirement")
                else:
                    # Create single DUT instance
                    device_instance = test_instance_t.device_instance_dict
                    device_type_obj = eval(device_instance["type"])
                    device_name = device_instance["name"]
                    device_parameters = device_instance.get("parameters")
                    if device_parameters:
                        device_object = device_type_obj(device_name, **device_parameters)
                    else:
                        device_object = device_type_obj(device_name)
                    TS.DUT = device_object
                    device_type = device_object.type
                    if device_type not in TS.requirement["DUT"]:
                        raise ValueError("Check DUT Requirement")

            # Check script-EQUIPMENT dependency
            if TS.requirement["EQUIPMENT"]:
                if isinstance(self.teststation_config["equipment"], list):
                    TS.EQUIPMENT = []
                    # Create multiple Equipment instance
                    for equipment_t in self.teststation_config["equipment"]:
                        if equipment_t["type"] in TS.requirement["EQUIPMENT"]:
                            # Create an equipment instance
                            equipment_type = eval(equipment_t["type"])
                            equipment_parameters = equipment_t.get("parameters")
                            equipment_name = equipment_t["name"]
                            # TODO: add modifyable name to each equipment
                            if equipment_parameters:
                                equipment_object = equipment_type(**equipment_parameters)
                            else:
                                equipment_object = equipment_type()
                            TS.EQUIPMENT.append(equipment_object)
                            if equipment_name not in TS.requirement["EQUIPMENT"]:
                                raise ValueError("Check Equipment Requirement")
                else:
                    # Create single Equipment instance
                    equipment_t = self.teststation_config["equipment"]
                    if equipment_t["type"] in TS.requirement["EQUIPMENT"]:
                        # Create an equipment instance
                        equipment_type = eval(equipment_t["type"])
                        equipment_parameters = equipment_t.get("parameters")
                        equipment_name = equipment_t["name"]
                        # TODO: add modifyable name to each equipment
                        if equipment_parameters:
                            equipment_object = equipment_type(**equipment_parameters)
                        else:
                            equipment_object = equipment_type()
                        TS.EQUIPMENT = equipment_object
                        if equipment_name not in TS.requirement["EQUIPMENT"]:
                            raise ValueError("Check Equipment Requirement")

            # Copy test parameters from test_config.yaml
            TS.params_from_testcfg = test_instance_t.params_from_testcfg

            # Add result path for the testcase
            TS.log_folder = self.log_folder

            # Save TS
            test_instance_t.TS = TS

    def qtest_publish(self, test_instance):
        """Publish results in qtest."""
        QTObject = QTestIntegration(self.qt_url, self.qt_username, self.qt_password, self.qt_project_id, self.qt_testcycle_id)
        QTObject.qt_write_test_log(test_instance.test_result.result_per_step, test_instance.test_result.result, test_instance.TS.automation_content)

    def qmetry_publish(self, test_suite):
        """Publish results in qtest."""
        test_instances = test_suite.test_instances
        qmetry_test_suite = []
        for test_instance in test_instances:
            test_case = {
                "start_time_": test_instance.start_time,
                "result_steps_": test_instance.test_result.result_per_step,
                "result_overall_": test_instance.test_result.result,
                "automation_content_": test_instance.TS.automation_content,
                "end_time_": test_instance.end_time,
            }
            qmetry_build_version = test_suite.build_version,
            qmetry_suite_name = test_suite.suite_tag
            qmetry_test_suite.append(test_case)
        try:
            QMObject = QmetryIntegration(self.qmetry_url, self.qmetry_automation_api_key, self.qmetry_openapi_key, self.qmetry_project_name, self.qmetry_exec_folder, qmetry_build_version)
            QMObject.post_test_result(qmetry_test_suite, qmetry_suite_name)
        except Exception as e:
            self.logger.error("Error during Qmetry result publishing: %s", str(e))
            print("Error during Qmetry result publishing: %s. Check autolog.txt. Skipping publishing...", str(e))

    def run_tests(self):
        """Run test cases."""
        # Create dependencies
        self.logger.info("Creating test dependencies")
        self._create_dependencies()
        # Run tests
        for test_instance in self.test_suite.test_instances:
            TS = test_instance.TS
            self.logger.info("=================== Starting test case: %s ===================", TS.name)
            self.setup(TS)
            try:
                test_instance.start_time = datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
                TS.initialize()
                TS.teststeps()
                TS.evaluate()
                test_instance.end_time = datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
                test_instance.test_result.result = TS.get_test_result()
                test_instance.test_result.result_per_step = TS.get_result_per_step()
                test_instance.test_result.suite_name = self.test_suite.suite_name
                test_instance.test_result.build_version = self.test_suite.build_version
                if self.qt_integration:
                    self.logger.info("Publish Result to qTest")
                    self.qtest_publish(test_instance)
                TS.wrapup()
                self.logger.info("Ending test case: %s", TS.name)
            except KeyboardInterrupt:
                self.logger.error("Test execution interrupted by user (KeyboardInterrupt).")
                print("Test execution interrupted by user. Exiting...")
                test_instance.end_time = datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
            except Exception as e:
                self.logger.error("Error during test case execution: %s", str(e))
                print("Error during test case execution: %s. Check autolog.txt", str(e))
                test_instance.end_time = datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
            self.teardown(TS)
            self.logger.info("Test Result: %s", test_instance.test_result.result)
        if self.qmetry_integration:
            self.logger.info("Publish Result to Qmetry")
            self.qmetry_publish(self.test_suite)
        # Create result data structure
        result_suite = ResultSuite(self.test_suite)
        test_result_raw = result_suite.get_raw_result()
        # Create HTML report
        self.logger.info("Creating HTML Report")
        report_abs_path = os.path.join(self.log_folder, self.html_report_filename)
        report_engine_html = ReportEngine(test_result_raw, template_directory=self.report_template_directory, template_filename=self.report_template_filename, report_filename=report_abs_path)
        report_engine_html.create_report_html()
        
    def run_post_processing(self, script_name, create_report=False, **params):
        """Run post-processing steps."""
        results_folder = self.log_folder
        test_suite_module = importlib.import_module("NSTA.testscripts.{}".format(script_name)) 
        script_object = eval("test_suite_module.{}".format(script_name))
        post_processing_script = script_object(results_folder, **params)
        post_processing_script.run_script()
        all_results = post_processing_script.get_result_suite()
        # Only use the specified results_folder
        results_base = os.path.join(os.path.dirname(NSTA.__file__), "results")
        folder = os.path.join(results_base, results_folder)
        analysis_report_path = os.path.join(folder, "analysis.html")
        # The template should be updated to use 'plot_image' if present in each result
        report_engine = ReportEngine(
            all_results,
            template_directory=self.report_template_directory,
            template_filename=self.report_template_filename,
            report_filename=analysis_report_path
        )
        report_engine.create_report_html()
        self.logger.info(f"Analysis report generated at: {analysis_report_path}")

    def run_tests_current(self):
        """Setup device for current measurement and run test cases."""
        # Create dependencies
        self.logger.info("Creating test dependencies")
        self._create_dependencies()
        # Run tests
        for test_instance in self.test_suite.test_instances:
            TS = test_instance.TS
            self.logger.info("=================== Starting test case: %s ===================", TS.name)
            # self.setup(TS)
            test_instance.start_time = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
            TS.initialize()
            TS.teststeps()
            TS.evaluate()
            test_instance.end_time = datetime.datetime.now().strftime("%Y%m%d %H:%M:%S.%f")[:-3]
            test_instance.test_result.result = TS.get_test_result()
            test_instance.test_result.result_per_step = TS.get_result_per_step()
            test_instance.test_result.result_output = TS.get_result_output()
            if self.qt_integration:
                self.logger.info("Publish Result to qTest")
                self.qtest_publish(test_instance)
            TS.wrapup()
            self.logger.info("Ending test case: %s", TS.name)
            # self.teardown(TS)
            self.logger.info("Test Result: %s", test_instance.test_result.result)
        # Create result data structure
        result_suite = ResultSuite(self.test_suite)
        test_result_raw = result_suite.get_raw_result()
        # Create HTML report
        self.logger.info("Creating HTML Report")
        report_abs_path = os.path.join(self.log_folder, self.html_report_filename)
        report_engine_html = ReportEngine(test_result_raw, template_directory=self.report_template_directory, template_filename=self.report_template_filename, report_filename=report_abs_path)
        report_engine_html.create_report_html()


def dummy_testrun():
    """Dummy testrun for sanity check."""
    TR = TestRun()
    TR.initialize()
    TR.run_tests()
    # TR.run_post_processing("trumi_log_parser", create_report=True, analysis_type=3)


def current_testrun():
    """Current testrun for current consumption suite."""
    TR = TestRun()
    TR.initialize()
    TR.run_tests_current()  # 80% accuracy


if __name__ == "__main__":
    # Example run
    dummy_testrun()
    # current_testrun()
