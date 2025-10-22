"""Interface module to the REST API Interface.

This module implements generic REST calls to be interfaced with relevant DUT's
and equipment.
"""


from time import sleep
import json
from urllib.parse import urljoin, urlparse
import requests


from NSTAX.interface.interface import Interface


class RESTAPIInterface(Interface):
    """Sensolus Connect REST API interface class.

    :param base_url: Base API URL
    :type base_url: str
    :param api_key: API key for the API account
    :type api_key: str
    """
    def __init__(self, base_url, api_key):
        super().__init__("RESTAPIInterface", version = 0.1)
        self.base_url = base_url
        self.api_key = f"?apiKey={api_key}"
        self.interface_wait_time = 1

    def _urljoin(self, url_segments=None):
        try:
            iter(url_segments)
        except TypeError:
            raise ValueError("URLs must be iterable!", f"URLs:{url_segments}")
        joined_url = ""
        for url_segment in url_segments:
            if joined_url:
                if not joined_url.endswith("/"):
                    joined_url = f"{joined_url}/"
            joined_url = urljoin(joined_url, url_segment)
        return joined_url

    def get(self, path):
        """Issues an HTTP GET message and returns the content.

        :param path: URL string following the baseurl
        :type path: str

        :return: Pythonic representation of the API Json response
        :rtype: dict, list, str, int, float, True, False, None
        """
        # Add trailing backslash if not present
        base_url_t = f"{self.base_url}/" if not self.base_url.endswith("/") else self.base_url
        url_wo_key = urljoin(base_url_t, path)
        requests_url = "{}{}".format(url_wo_key.rstrip("/"), self.api_key)  # Strip trailing backslash if there before adding the key
        response = requests.get(requests_url)
        response.close()
        if not response.ok:
            raise ValueError("Error in Get command !", response.status_code, response.reason, response.content)
        self.logger.info("Response: %s, via interface: %s", json.loads(response.text), type(self).__name__)
        return json.loads(response.text)

    def post(self):
        """API HTTP POST message.

        TODO: implement.
        """

    def connect(self):
        """Connects to the API Interface.

        Note: No explicit connection is needed for the current implimentation,
        therefore simply checking the connection out using HEAD."""
        self.logger.info("Connecting to the interface: %s", type(self).__name__)
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

    def disconnect(self):
        """Disconnect from the API interface.

        Note: No explicit disconnection is needed for the current implimentation.
        """
        self.logger.info("Disconnecting from the interface: %s", type(self).__name__)
        self.connected = False


if __name__ == "__main__":
    # Example run
    RAI = RESTAPIInterface("https://stickntrack.sensolus.com/rest/api/v2", "bc5ffd3c423f4625831f41a6f3ae28ac")
    RAI.connect()
    print(RAI.get("devices/M9RDJA"))
    RAI.disconnect()
