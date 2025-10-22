"""Base module for for test scripts.

This module contains the base class for any to-be test scripts. All new test
scripts are to be inherited from this.

Contents of this modules are not for instantiation.
"""


import logging


class ResultClassifier:
    """Test result classifier."""
    def __init__(self):
        self.NO_OP = 0
        self.NOT_RUN = 1
        self.PASSED = 2
        self.FAILED = 4
        self.INCOMPLETE = 8
        self.BLOCKED = 16

    def get_result_string(self, result_input):
        """Reverse search classifiers from result.

        :param result_input: Numerical test result
        :type result_input: int

        :return: String representation of the test result, None of not found
        :rtype: str, or None
        """
        for key, val in self.__dict__.items():
            if val == result_input:
                return key
        return None


class TestScript:
    """Base class to be inherited for new test case implementation."""
    def __init__(self):
        # Visual
        self.name = ""
        self.version = "0.0"
        self.description = ""
        # self.requirement = {}
        self.automation_content = None
        self.requirement = {
            "DUT": [],
            "EQUIPMENT": [],
        }
        self.params_from_testcfg = {}
        self.testpoints = []        # Container of the testcases
        self.DUT = None
        self.EQUIPMENT = None
        self.n_steps = 0            # # test steps
        self.current_step = None    # Current test step
        self.result_step = {}       # Result per test step
        self.result = 0             # Overall test result
        self.result_classifier = ResultClassifier()

        self.logger = logging.getLogger('NSTA.{}'.format(__name__))

    def initialize(self):
        """Init routine, runs before going through test steps."""
        # TODO: Remove dependencies on n_steps, can be handled during postprocessing as well
        result_template = {
            "actual_result": "Not Run",
            "verdict": self.result_classifier.NOT_RUN
        }
        for i in range(self.n_steps):
            self.result_step[1 + i] = result_template.copy()

    def teststeps(self):
        """Test steps as defined by test spec."""

    def evaluate(self):
        """Result evaluation after test steps."""
        result = 0
        for index, result_step in self.result_step.items():
            result |= result_step["verdict"]
        # Current choice for calculating overall result:
        # RES_FAILED > RES_BLOCKED > RES_INCOMPLETE > RES_NOT_RUN > RES_PASSED
        if result & self.result_classifier.FAILED:
            result = self.result_classifier.FAILED
        elif result & self.result_classifier.BLOCKED:
            result = self.result_classifier.BLOCKED
        elif result & self.result_classifier.INCOMPLETE:
            result = self.result_classifier.INCOMPLETE
        elif result & self.result_classifier.NOT_RUN:
            result = self.result_classifier.NOT_RUN
        elif result & self.result_classifier.PASSED:
            result = self.result_classifier.PASSED
        self.result = result

    def wrapup(self):
        """Wrapup routine, runs after completion of test steps."""

    def save_step(self, step_index, step_description, expected_result, actual_result, verdict):
        """Save test step.
        :param step_index: Incremental test step number [1...N]
        :type step_index: int
        :param step_description: One liner on what is to be done in this step
        :type step_description: str
        :param expected_result: Expected result
        :type expected_result: str
        :param actual_result: Actual result
        :type actual_result: str
        :param verdict: Test result for this step as classified in ResultClassifier
        :type verdict: ResultClassifier.X
        """
        self.result_step[step_index] = {}
        self.result_step[step_index]["step_description"] = step_description
        self.result_step[step_index]["expected_result"] = expected_result
        self.result_step[step_index]["actual_result"] = actual_result
        self.result_step[step_index]["verdict"] = verdict
        self.logger.info("Step %s: Expected: %s, Actual: %s, Verdict: %s", step_index, expected_result, actual_result, verdict)

    def step_start(self, step_no, step_description, expected_result):
        """Log the start of a test step."""
        self.current_step = {
            "step_no": step_no,
            "step_description": step_description,
            "expected_result": expected_result
        }
        self.logger.info("Step %d: %s", step_no, step_description)

    def step_start(self, step_no, step_description, expected_result):
        """Log the start of a test step."""
        self.current_step = {
            "step_no": step_no,
            "step_description": step_description,
            "expected_result": expected_result
        }
        self.logger.info("Step %d: %s", step_no, step_description)
        
    def step_end(self, actual_result, step_verdict):
        """Log the end of a test step and save the results."""
        if self.current_step is None:
            self.logger.error("No current step to end. Please call step_start first.")
            return
        
        step_no = self.current_step["step_no"]
        step_description = self.current_step["step_description"]
        expected_result = self.current_step["expected_result"]
        
        if step_verdict == "PASSED":
            step_verdict = self.result_classifier.PASSED
        elif step_verdict == "FAILED":
            step_verdict = self.result_classifier.FAILED
        elif step_verdict == "INCOMPLETE":
            step_verdict = self.result_classifier.INCOMPLETE
        elif step_verdict == "BLOCKED":
            step_verdict = self.result_classifier.BLOCKED   
        elif step_verdict == "NOT_RUN":
            step_verdict = self.result_classifier.NOT_RUN  
        else:
            self.logger.error("Invalid step verdict: %s", step_verdict)
            return
        
        self.save_step(step_no, step_description, expected_result, actual_result, step_verdict)
        self.current_step = None  # Reset current step after ending it
    
    def get_test_result(self):
        """Returns current test result."""
        return self.result

    def get_result_per_step(self):
        """Returns current test result over each step run."""
        return self.result_step
    

class PostProcessingScript:
    """Class to run any object with a run_script method."""
    def __init__(self, script_obj):
        self.script_obj = script_obj

    def execute(self, *args, **kwargs):
        if hasattr(self.script_obj, "run_script") and callable(getattr(self.script_obj, "run_script")):
            return self.script_obj.run_script(*args, **kwargs)
        else:
            raise AttributeError("The provided object does not have a callable run_script method.")