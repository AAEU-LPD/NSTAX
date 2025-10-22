"""Analyze Cell Provider Specific Performance Paramters.

This standalone script:
    1. Crawls through all devices in a platform organization within given timeframe
    2. analyzes ECL stats of all devices from NB-Iot diagnostic messages
    3. Generates a python dictionary highlighting network providers' field perfromance wrt ECL values
    4. Optionally, creates a HTML report separated by providers

Makes use of the following features of the NSTA framework:
    1. SensolusWebInterface: For accessing the platform
    2. PlatformDevice: To get device specific messages
    3. ReportEngine: Makes use of jinja2 HTML reporting
"""


from NSTAX.interface.sensolus_web_interface import SensolusWebInterface
from NSTAX.devices.platform_device import PlatformDevice
from NSTAX.reports.report_engine import ReportEngine


class NBIOTECLStatsOverContract:
    """Check ECL level Stats Per Provider For All Trackers in Org Level.

    Note: API call heavy, check usages limits

    Pre-conditions:
        - Access to AlpsAlpine API Platform

    :param org_id: Platform Org ID
    :type raw_message: int
    :param start_time_utc: Start Diagnostic Period in ISO 8601 UTC format
    :type start_time_utc: str
    :param end_time_utc: End Diagnostic Period in ISO 8601 UTC format
    :type end_time_utc: str
    :param max_n_devices: Max. number of devices in this org returned, defaults to 1000
    :type max_n_devices: int, optional
    :param max_n_messages: Max. number of messages returned, defaults to 500
    :type max_n_messages: int, optional
    """
    def __init__(self, org_id, start_time_utc, end_time_utc, max_n_devices=1000, max_n_messages=500):
        self.version = 0.1
        self.org_id = org_id
        self.start_time_utc = start_time_utc
        self.end_time_utc = end_time_utc
        self.max_n_devices = max_n_devices
        self.max_n_messages = max_n_messages
        self.cell_provider_stats = {}
        self._run_steps()
        self._post_process()

    def _process_device_data(self, device_id):
        device_instance = PlatformDevice(device_id)
        # Connect to the device instance
        device_instance.connect()
        # Get cell provider
        cell_provider = device_instance.get_cellular_provider()
        # Get backend messages
        backend_messages = device_instance.get_messages(start_time_utc=self.start_time_utc, end_time_utc=self.end_time_utc, max_n_messages=self.max_n_messages)
        print (len(backend_messages))
        # Disconnect from the device instance
        device_instance.disconnect()
        # Compile diagnostic messages with ECL data
        diag_messages = []
        for message_ in backend_messages:
            try:
                # Brutforce, ignore wrong formats, not recommended. See other scripts for good implememtations
                message_type = message_["decodedMsg"]["messageType"]
            except KeyError:
                message_type = ""
            if message_type == "NBIOT_DIAGNOSTICS":
                if "ecl" in message_["decodedMsg"]["data"]:
                    diag_messages.append(message_)
        # Organize ECL levels to the device info
        ecl_stats_template = {
            0: 0,
            1: 0,
            2: 0,
            255: 0,
            "INVALID_VALUE": 0,
            "DECODER_ERROR": 0
        }
        current_ecl_counter = ecl_stats_template.copy()
        for diag_message in diag_messages:
            try:
                meas_ecl = int(diag_message["decodedMsg"]["data"]["ecl"])
            except KeyError:
                current_ecl_counter["DECODER_ERROR"] += 1
            except ValueError:
                current_ecl_counter["INVALID_VALUE"] += 1
            else:
                if meas_ecl in current_ecl_counter:
                    current_ecl_counter[meas_ecl] += 1
                else:
                    current_ecl_counter["INVALID_VALUE"] += 1
        # Update data on the cell specific structure
        if cell_provider not in self.cell_provider_stats:
            # First occurrance
            self.cell_provider_stats[cell_provider] = {"number_of_devices": 0, "number_of_diag_messages":0, "ecl_stats": ecl_stats_template.copy()}
        # Increment device counter from this provider
        self.cell_provider_stats[cell_provider]["number_of_devices"] += 1
        self.cell_provider_stats[cell_provider]["number_of_diag_messages"] += len(diag_messages)
        # Update ecl stats for this provider
        for level_, counter_ in current_ecl_counter.items():
            self.cell_provider_stats[cell_provider]["ecl_stats"][level_] += counter_

    def _run_steps(self):
        # Connect to backend
        SWI = SensolusWebInterface()
        SWI.connect()
        # Get list of devices in org:
        # Works params_ = {'maxResults': self.max_n_devices, 'sort': '[{"property": "lastActivity", "direction": "DESC"}]', 'query': [{'categoryId': 'assetInfo', 'filterKey': 'deviceIdentifier', 'filterType': 'MULTI_STRING', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'trackerStatus', 'filterKey': 'trackerStatus', 'filterType': 'MULTI_SELECT_CHECKBOX', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'batteryInfo', 'filterKey': 'remainingBattery', 'filterType': 'NUMERIC', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'userInfo', 'filterKey': 'organizations', 'filterType': 'MULTI_SELECT_AUTO_COMPLETE', 'searchType': 'STATIC', 'notFilter': False, 'filterValue': {'includeEmpty': False, 'includeNoEmpty': False, 'selectedValues': [self.org_id]}}, {'categoryId': 'assetInfo', 'filterKey': 'deviceCategory', 'filterType': 'MULTI_SELECT_CHECKBOX', 'searchType': 'STATIC', 'notFilter': False, 'filterValue': {'includeEmpty': False, 'includeNoEmpty': False, 'selectedValues': ['TRACKER']}}], 'queryObjectType': 'SIGFOX_DEVICE', 'requestedTableColumns': [{'columnKey': 'name', 'order': 0}, {'columnKey': 'serial', 'order': 0}, {'columnKey': 'deviceTag', 'order': 0}, {'columnKey': '_ownedName', 'order': 0}, {'columnKey': 'status', 'order': 0}, {'columnKey': 'remainingBattery', 'order': 0}, {'columnKey': 'thirdPartyId', 'order': 0}, {'columnKey': 'lastLocationSource', 'order': 0}, {'columnKey': 'lastSeenAlive', 'order': 0}, {'columnKey': 'lastActivity', 'order': 'DESC'}, {'columnKey': 'lastActivityTimestamp', 'order': 0}, {'columnKey': 'address', 'order': 0}], 'searchQueryType': 'BASIC', 'startIndex': 0}
        params_ = {'maxResults': self.max_n_devices, 'sort': '[{"property": "lastActivity", "direction": "DESC"}]', 'query': [{'categoryId': 'assetInfo', 'filterKey': 'deviceIdentifier', 'filterType': 'MULTI_STRING', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'trackerStatus', 'filterKey': 'trackerStatus', 'filterType': 'MULTI_SELECT_CHECKBOX', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'batteryInfo', 'filterKey': 'remainingBattery', 'filterType': 'NUMERIC', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'userInfo', 'filterKey': 'organizations', 'filterType': 'MULTI_SELECT_AUTO_COMPLETE', 'searchType': 'STATIC', 'notFilter': False, 'filterValue': {'includeEmpty': False, 'includeNoEmpty': False, 'selectedValues': [self.org_id]}}, {'categoryId': 'assetInfo', 'filterKey': 'deviceCategory', 'filterType': 'MULTI_SELECT_CHECKBOX', 'searchType': 'STATIC', 'notFilter': False, 'filterValue': {'includeEmpty': False, 'includeNoEmpty': False, 'selectedValues': ['TRACKER']}}], 'queryObjectType': 'SIGFOX_DEVICE', 'requestedTableColumns': [{'columnKey': 'name', 'order': 0}, {'columnKey': 'serial', 'order': 0}, {'columnKey': 'deviceTag', 'order': 0}, {'columnKey': '_ownedName', 'order': 0}, {'columnKey': 'status', 'order': 0}, {'columnKey': 'remainingBattery', 'order': 0}, {'columnKey': 'thirdPartyId', 'order': 0}, {'columnKey': 'lastLocationSource', 'order': 0}, {'columnKey': 'lastSeenAlive', 'order': 0}, {'columnKey': 'lastActivity', 'order': 'DESC'}, {'columnKey': 'lastActivityTimestamp', 'order': 0}, {'columnKey': 'address', 'order': 0}], 'searchQueryType': 'BASIC', 'startIndex': 0}
        response_dict = SWI.post("/rest/sigfoxdevices/filter/search", data=params_, return_response=True)
        # Close connection
        SWI.disconnect()
        device_list = response_dict["data"]
        # Update with device info
        for device_ in device_list:
            device_id_ = device_['id']
            self._process_device_data(device_id_)

    def _post_process(self):
        # Postprocess overall data
        for provider_, detailed_stats_ in self.cell_provider_stats.items():
            self.cell_provider_stats[provider_]["ecl_stats_in_percentage"] = {
                0: 0,
                1: 0,
                2: 0,
                255: 0,
                "INVALID_VALUE": 0,
                "DECODER_ERROR": 0
            }
            n_readouts = detailed_stats_["number_of_diag_messages"]
            for level_, ctr_ in detailed_stats_["ecl_stats"].items():
                self.cell_provider_stats[provider_]["ecl_stats_in_percentage"][level_] = round((100 * ctr_ / n_readouts), 2)

    def return_stats(self):
        """
        Get Provider Stats in Dictionary Form

        :returns: Prover Stats
        :rtype: dict
        """
        return self.cell_provider_stats

    def generate_html_report(self, template_directory, template_filename, report_filename):
        """
        Generates HTML Report Using jinja2 Compatible Template

        :param template_directory: HTML Template Directory (Absolute Path)
        :type template_directory: str
        :param template_filename: HTML Template Filename (Filename Only, No Path)
        :type template_filename: str
        :param report_filename: Resulting Report Filename (Absolute Path)
        :type report_filename: str
        """
        report_engine_html = ReportEngine(self.cell_provider_stats, template_directory, template_filename, report_filename)
        report_engine_html.create_report_html()


if __name__ == "__main__":
    # Main Function, User inputs are to be updated only here
    ORG_ID = 3861   # Alps N5 dev Team
    # ORG_ID = 3807   # Max-Boegl Connect
    START_TIME_UTC = "2023-10-21T00:00:00"
    END_TIME_UTC = "2024-01-17T00:00:00"
    MAX_N_DEVICES = 10
    MAX_N_MESSAGES = 500
    test_script = NBIOTECLStatsOverContract(ORG_ID, START_TIME_UTC, END_TIME_UTC, MAX_N_DEVICES, MAX_N_MESSAGES)
    # print ("Stat: ", test_script.return_stats())
    # Generate HTML Report
    TEMPLATE_DIRECTORY = "C:/UserData/dev/NSTA/standalone_scripts/netstat_org"
    TEMPLATE_FILENAME = "report_template_eclstats_org.html"
    REPORT_FILENAME = "C:/UserData/dev/NSTA/standalone_scripts/netstat_org/report_.html"
    test_script.generate_html_report(TEMPLATE_DIRECTORY, TEMPLATE_FILENAME, REPORT_FILENAME)
