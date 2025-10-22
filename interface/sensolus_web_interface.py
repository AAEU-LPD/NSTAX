"""Interface module to Sesolus stickntrack web sessions.

Primary purpose of this module is to interface stickntrack to retrieve raw FW
messages.

Note: This is NOT the usage of the official Sensolus Connect API, raher a rest
API based web session replication.
"""


from time import sleep
import json
from urllib.parse import urljoin, urlparse
import requests
import yaml


from NSTAX.interface.interface import Interface


class SensolusWebInterface(Interface):
    """Web session of Sensolus.
    """
    def __init__(self):
        super().__init__("SensolusWebInterface", version = 0.1)
        self.base_url = self.auth_path = self.auth_username = self.auth_password = ""
        self.teststation_config_file = "../NSTA/config/teststation_config.yaml"
        self._get_configuration()
        self.session = requests.Session()
        self.interface_wait_time = 1
        self.headers = {'X-Csrf-Token':'123'}

    def connect(self):
        """Connects to the Web Interface.
        """
        self.logger.info("Connecting to the interface: %s", type(self).__name__)
        if self.auth_path:
            # Authenticate
            auth_url = self._urljoin(url_segments=(self.base_url, self.auth_path)).rstrip("/") + "/"
            response = self.session.post(f"{auth_url}{self.auth_username}?_csrf=undefined", data=self.auth_password)
            if response.ok:
                self.connected = True
                # saving token 
                response_data = json.loads(response.content)
                x_csrf_token_value = response_data['csrfToken']
                self.headers = {'X-Csrf-Token':x_csrf_token_value}                             
            else:
                self.connected = False
                self.logger.info("Error Authentication, check url and login credentials")
        else:
            # Check existence of the netloc
            parsed_url = urlparse(self.base_url)
            url_root = f"{parsed_url.scheme}://{parsed_url.netloc}"
            try:
                requests.head(url_root)
                sleep(self.interface_wait_time)
                self.connected = True
            except requests.exceptions.ConnectionError as e_:
                self.connected = False
                self.logger.info("Error connecting to the interface: %s via URL: %s", type(self).__name__, url_root)

    def get(self, path, parameters=None):
        """Issues an HTTP GET message and returns the content.

        :param path: URL string following the baseurl
        :type path: str
        :param parameters: Dictionary of url parameters, defaults to None
        :type parameters: dict, optional

        :return: Pythonic representation of the API Json response
        :rtype: dict, list, str, int, float, True, False, None
        """
        base_url_t = self.base_url.rstrip("/") + "/"
        requests_url = urljoin(base_url_t, path)
        response = self.session.get(requests_url, params=parameters)
        response.close()
        if not response.ok:
            raise ValueError("Error in Get command !", response.status_code, response.reason, response.content)
        response_text = self._load_json_response_text(response.text)
        #self.logger.info("Response: %s, via interface: %s", response_text, type(self).__name__)
        return response_text

    def post(self, path, data):
        """Issues an HTTP POST message.

        :param path: URL string following the baseurl
        :type path: str
        :param data: json data to send in the body of the request dictionary of url parameters
        :type data: dict
        """
        # adding  csrfToken
        base_url_t = self.base_url.rstrip("/") + "/"
        requests_url = urljoin(base_url_t, path)
        response = self.session.post(requests_url, headers=self.headers, json=data)
        response.close()
        if not response.ok:
            raise ValueError("Error in Post command !", response.status_code, response.reason, response.content)
        response_text = self._load_json_response_text(response.text)
        self.logger.info("Response: %s, via interface: %s", response_text, type(self).__name__)
        return response.ok

    def delete(self, path, parameters=None):
        """Issues an HTTP DELETE message.

        :param path: URL string following the baseurl
        :type path: str
        :param parameters: Dictionary of url parameters, defaults to None
        :type parameters: dict, optional

        :return: Pythonic representation of the API Json response
        :rtype: dict, list, str, int, float, True, False, None
        """
        base_url_t = self.base_url.rstrip("/") + "/"
        requests_url = urljoin(base_url_t, path)
        response = self.session.delete(requests_url, headers=self.headers, params=parameters)
        response.close()
        if not response.ok:
            raise ValueError("Error in Delete command !", response.status_code, response.reason, response.content)
        response_text = self._load_json_response_text(response.text)
        self.logger.info("Response: %s, via interface: %s", response_text, type(self).__name__)
        return response_text
        

    def _load_json_response_text(self, response_json_str):
        try:
            resp_str = json.loads(response_json_str)
        except json.decoder.JSONDecodeError as e_:
            resp_str = ""
        return resp_str

    def _urljoin(self, url_segments=None):
        try:
            iter(url_segments)
        except TypeError as e_:
            raise ValueError("URL list must be iterable!", f"URLs:{url_segments}")
        joined_url = ""
        for url_segment in url_segments:
            if joined_url:
                if not joined_url.endswith("/"):
                    joined_url = f"{joined_url}/"
            joined_url = urljoin(joined_url, url_segment)
        return joined_url

    def _get_configuration(self):
        base_url = auth_path = auth_username = auth_password = ""
        with open(self.teststation_config_file, 'r') as data_stream:
            try:
                ts_config = yaml.safe_load(data_stream)
                try:
                    base_url = ts_config["stickntrack"]["url"]
                    auth_path = ts_config["stickntrack"]["auth_path"]
                    auth_username = ts_config["stickntrack"]["username"]
                    auth_password = ts_config["stickntrack"]["password"]
                except KeyError as error_:
                    print (error_)
            except yaml.YAMLError as error_:
                print(error_)
        self.base_url = base_url
        self.auth_path = auth_path
        self.auth_username = auth_username
        self.auth_password = auth_password

    def disconnect(self):
        """Close web interfaces session.
        """
        self.logger.info("Disconnecting from the interface: %s", type(self).__name__)
        self.session.close()
        self.connected = False


if __name__ == "__main__":
    # Example run
    """ Add the following inputs in ../config/teststation_config.yaml
        stickntrack:
          url: "https://stickntrack.sensolus.com"
          auth_path: "/rest/authentication/login"
          username: "your_username"
          password: "your_password"
    """
    SWI = SensolusWebInterface()
    SWI.connect()
    # response_dict = SWI.get("/rest/sigfoxdevices/341506/sigfoxMessages", parameters={"start": 0, 'limit': 5, 'from_date': '2022-08-01T00:00:00+02:00', 'to_date': '2022-08-31T23:59:59+02:00', 'not_filter': False})
    # response_dict = SWI.get("/rest/sigfoxdevices/436825/sigfoxMessages", parameters={"start": 0, 'limit': 5, 'from_date': '2023-02-16T16:50:00+00:00', 'to_date': '2023-02-16T16:58:00+00:00', 'not_filter': False})
    # SWI.post("/rest/device_setting_queue", data = {"deviceId": 374158, "bidirPayload": "b007e00000000006", "description": "Set DL Interval to 5 Hours"})
    FOTA_DATA = {
        "operationType":"QUEUE_FIRMWARE_UPGRADE",
        "devices":["436826"],
        "queueFirmwareUpgrade":{
            "queueFirmwareUpgradeOption":"NBIOT",
            "queueFirmwareUpgradeVersion":"ALL",
            "firmwareShaKey":"FWUP_PKG_LYKN5_ALPS_Debug_abbb4ee5_v22.3.0_N5_Alps_Generic_activated.bin",
            "clearPendingFirmwareUpgrade":False}
        }
    SWI.post("/rest/bulk_device_operations/TRACKER", data = FOTA_DATA)
    SWI.disconnect()
    # Pretty print
    # from pprint import pprint
    # pprint(response_dict)
