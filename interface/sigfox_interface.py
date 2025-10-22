"""Interface module to the Sigfox API.

Purpose of this module is to control Sigfox REST API connections for arbitrary
DUTs.
"""


from time import sleep
import json
from urllib.parse import urljoin
import requests
import yaml

from NSTA.interface.interface import Interface


class SigfoxInterface(Interface):
    """Sigfox API interface class.
    """
    def __init__(self):
        super().__init__("Sigfox", version = 0.1)
        self.teststation_config_file = "../NSTA/config/teststation_config.yaml"
        self.auth = self._get_credentials()
        self.baseurl = "https://api.sigfox.com/v2"
        self.interface_wait_time = 1    # Avoid Error 429: "Sorry this api access is limited to : 1r / 1s"

    def get(self, message_string, parameters=None):
        """Issue an Sigfox API HTTP GET message and returns the content.

        :param message_string: url string followed by the baseurl
        :type message_string: str
        :param parameters: parameters part of the Sigfox API
        :type parameters: dict

        :return: Dict representation of the API Json response
        :rtype: dict
        """
        if not parameters:
            parameters = {}
        requestsurl = self._urljoin(url_segments=(self.baseurl, message_string))
        logger_data = f"GET url: {requestsurl}, with parameters: {parameters}, via interface: {type(self).__name__}"
        self.logger.info(logger_data)
        response = requests.get(requestsurl, auth=self.auth, params=parameters)
        response.close()    # Free the active port
        if not response.ok:
            raise ValueError("Error in Get command !", response.status_code, response.reason, response.content)
        sleep(self.interface_wait_time)
        self.logger.info("Response via interface %s: %s", type(self).__name__, response.text)        
        return json.loads(response.text)

    def post(self):
        """API HTTP POST message.

        TODO: Implement.
        """

    def connect(self):
        """Connects to the Sigfox Interface.

        Note: No explicit connection is needed for the current implimentation,
        therefore simply checking the connection out."""
        self.logger.info("Connecting to the interface: %s", type(self).__name__)
        r_data = self.get("coverages/global/predictions", parameters={"lat": 48.28727848006257, "lng": 11.569482913704437})
        sleep(self.interface_wait_time)
        self.connected = True

    def disconnect(self):
        """Dummy disconnect."""
        self.logger.info("Disconnecting from the interface: %s", type(self).__name__)
        self.connected = False

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
            if url_segment.startswith("/"):
                url_segment_t = url_segment.lstrip("/")
            else:
                url_segment_t = url_segment
            joined_url = urljoin(joined_url, url_segment_t)
        return joined_url

    def _get_credentials(self):
        login_id, password = ("", "")
        with open(self.teststation_config_file, 'r') as data_stream:
            try:
                ts_config = yaml.safe_load(data_stream)
                try:
                    login_id, password = ts_config["sigfox"]["login_id"], ts_config["sigfox"]["password"]
                except KeyError as error_:
                    print (error_)
            except yaml.YAMLError as error_:
                print(error_)
        return (login_id, password,)


if __name__ == "__main__":
    # Example run
    SFI = SigfoxInterface()
    SFI.connect()
    sigfox_id = "21E71E6"
    command_url = f"devices/{sigfox_id}"
    print(f"Device Info of {sigfox_id}: {SFI.get(command_url)}")
    SFI.disconnect()
