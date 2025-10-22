"""Report Engine for static test report.

This module takes the framework's test result data structure as input and
creates static reports as per need.
"""


from jinja2 import Environment, FileSystemLoader


class ReportEngine:
    """Report engine base class.

        :param test_result_suite: Test result input
        :type test_result_suite: dict
        :param template_directory: jinja2 template directory
        :type template_directory: str
        :param template_filename: jinja2 template file
        :type template_filename: str
        :param report_filename: HTML report file
        :type report_filename: str
        :param text_encoding: encoding scheme for report, defaults to utf-8
        :type text_encoding: str, optional
    """
    def __init__(self, test_result_suite, template_directory, template_filename, report_filename, text_encoding="utf-8"):
        self.result_suite = test_result_suite
        self.template_directory = template_directory
        self.template_filename = template_filename
        self.report_filename = report_filename
        self.text_encoding = text_encoding
        self._initialize()

    def _initialize(self):
        # Open template
        j2_env = Environment(loader=FileSystemLoader(self.template_directory), trim_blocks=True)
        self.file_stream = j2_env.get_template(self.template_filename).render(result=self.result_suite)

    def create_report_html(self):
        """Creates HTML test report."""
        with open(self.report_filename, mode="w", encoding=self.text_encoding) as file_:
            print(self.file_stream, file=file_)


if __name__ == "__main__":
    # Demo caller
    sample_result_suite = {
        "name": "demo_testscript",
        "test_instances": [
            {
                "description": "Test Instance 1",
                "name": "NBIOTULMessageCheckDevice1",
                "dut_info": {"type":"NBIOT","name":"HATI"},
                "version": 0.1,
                "dut_info": None,
                "result_output": None,
                "result": "PASSED",
                "result_output": {"table":"","image":""},
                "result_step": {
                    "1": {
                        "step_description": "Activate the device",
                        "expected_result": "Device activated",
                        "actual_result": "Device activated",
                        "verdict": "PASSED"
                    },
                    "2": {
                        "step_description": "Check for activation message",
                        "expected_result": "Visible backend message: c87d",
                        "actual_result": "Message matched (c87d)",
                        "verdict": "FAILED"
                    },
                    "3": {
                        "step_description": "Check for DL ACK message",
                        "expected_result": "Visible backend message: f04100",
                        "actual_result": "Message matched (f04100)",
                        "verdict": "INCOMPLETE"
                    },
                },
            },
            {
                "description": "Test Instance 2",
                "name": "NBIOTULMessageCheckDevice2",
                "dut_info": {"type":"NBIOT","name":"HATI"},
                "result_output": {"table":"","image":""},
                "type": "NBIOT",
                "version": 0.1,
                "dut_info": None,
                "result_output": None,
                "result": "FAILED",
                "result_step": {
                    "1": {
                        "step_description": "Activate the device",
                        "expected_result": "Device activated",
                        "actual_result": "Device activated",
                        "verdict": 2
                    },
                    "2": {
                        "step_description": "Check for activation message",
                        "expected_result": "Visible backend message: c87d",
                        "actual_result": "Message matched (c87d)",
                        "verdict": 2
                    },
                    "3": {
                        "step_description": "Check for DL ACK message",
                        "expected_result": "Visible backend message: f04100",
                        "actual_result": "Message matched (f04100)",
                        "verdict": 2
                    },
                },
            }
        ]
    }
    report_engine = ReportEngine(sample_result_suite, template_directory="../reports/", template_filename="report_template.html", report_filename="test_report.html")
    report_engine.create_report_html()
