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


class DevSerToId:
    def __init__(self, org_id, serial_list):
        self.version = 0.1
        self.org_id = org_id
        self.serial_list = serial_list
        self.serial_id_map = {}
        self._run()

    def _run(self):
        SWI = SensolusWebInterface()
        SWI.connect()
        # Get list of devices in org:
        # Works params_ = {'maxResults': self.max_n_devices, 'sort': '[{"property": "lastActivity", "direction": "DESC"}]', 'query': [{'categoryId': 'assetInfo', 'filterKey': 'deviceIdentifier', 'filterType': 'MULTI_STRING', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'trackerStatus', 'filterKey': 'trackerStatus', 'filterType': 'MULTI_SELECT_CHECKBOX', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'batteryInfo', 'filterKey': 'remainingBattery', 'filterType': 'NUMERIC', 'searchType': 'STATIC', 'notFilter': False}, {'categoryId': 'userInfo', 'filterKey': 'organizations', 'filterType': 'MULTI_SELECT_AUTO_COMPLETE', 'searchType': 'STATIC', 'notFilter': False, 'filterValue': {'includeEmpty': False, 'includeNoEmpty': False, 'selectedValues': [self.org_id]}}, {'categoryId': 'assetInfo', 'filterKey': 'deviceCategory', 'filterType': 'MULTI_SELECT_CHECKBOX', 'searchType': 'STATIC', 'notFilter': False, 'filterValue': {'includeEmpty': False, 'includeNoEmpty': False, 'selectedValues': ['TRACKER']}}], 'queryObjectType': 'SIGFOX_DEVICE', 'requestedTableColumns': [{'columnKey': 'name', 'order': 0}, {'columnKey': 'serial', 'order': 0}, {'columnKey': 'deviceTag', 'order': 0}, {'columnKey': '_ownedName', 'order': 0}, {'columnKey': 'status', 'order': 0}, {'columnKey': 'remainingBattery', 'order': 0}, {'columnKey': 'thirdPartyId', 'order': 0}, {'columnKey': 'lastLocationSource', 'order': 0}, {'columnKey': 'lastSeenAlive', 'order': 0}, {'columnKey': 'lastActivity', 'order': 'DESC'}, {'columnKey': 'lastActivityTimestamp', 'order': 0}, {'columnKey': 'address', 'order': 0}], 'searchQueryType': 'BASIC', 'startIndex': 0}

        # "/sigfoxdevices/idsBySerial"
        response_dict = SWI.post("/rest/sigfoxdevices/idsBySerial", data={})
        # Close connection
        SWI.disconnect()
        


if __name__ == "__main__":
    # Main Function, User inputs are to be updated only here
    ORG_ID = 3861   # Alps N5 dev Team
    DEV_SERIAL = ["11UMAY",]
    
    
    test_script = DevSerToId (ORG_ID, DEV_SERIAL)
    print(test_script.serial_id_map)
