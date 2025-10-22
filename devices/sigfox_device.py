""" Device module for Sigfox suported devices.

Purpose of this module is to represent a device that is connected to different
interfaces such as: Sigfox backend, PPK2 interface.
"""


import datetime
import pandas as pd

from NSTA.devices.device import Device
from NSTA.interface.sigfox_interface import SigfoxInterface
from NSTA.equipment.PPKII import current_measure_ppk2
from NSTA.testscripts.lykaner5_current_detect import CurrentDetector, CurrentGraphPlotter


class SigfoxDevice(Device):
    """Sigfox device class.

    :param name: Unique name label of device
    :type name: str
    :param sigfox_id: 6 hex-digit Sigfox ID, defaults to ""
    :type sigfox_id: str, optional
    """

    def __init__(self, name, sigfox_id=""):
        super().__init__("SigfoxDevice", version=0.1)
        self.sigfox_id = sigfox_id
        self.name = name
        self.interface = None

        self.current_states = pd.DataFrame()
        self.current_states["indmin"] = ""
        self.current_states["indmax"] = ""

    def connect(self):
        """Connect to the device interface."""
        self.logger.info("Establish Sigfox connection for the device: {}".format(self.sigfox_id))
        self.interface = SigfoxInterface()
        self.interface.connect()

    def disconnect(self):
        """Disconnect from the device interface."""
        self.logger.info("Disconnecting the Sigfox device: {}".format(self.sigfox_id))
        self.interface.disconnect()

    def if_device_exists(self):
        """Checks if the device exists and accessible in the target Sigfox account.

        :returns: True for being connected, False otherwise.
        :rtype: bool
        """
        try:
            self.get_messages()
            # TODO: Use get_device_info() instead
        except ValueError:
            return False
        return True

    def get_device_info(self):
        """Get generic device info for connection check.

        :returns: Device info
        :rtype: dict
        """
        command = f"devices/{self.sigfox_id}"
        self.logger.info("Retrieve info with command: %s" % command)
        r_data = self.interface.get(command)
        self.logger.info("Device info received: %s" % r_data)
        return r_data

    def _get_epoach_time(self, sf_timestamp):
        """ Converts timestamp strings to Unix Epoch.

        :param sf_timestamp: Timestamp string as got from Sigfox backend. Format: "YYYY-MM-SS HH:MM:SS"
        :type sf_timestamp: str

        :return: Unix Epoch time in ms
        :rtype: int
        """
        try:
            ts_datetime = datetime.datetime.strptime(sf_timestamp, "%Y-%m-%d %H:%M:%S")
        except ValueError as e_:
            self.logger.warning(str(e_))
            return None
        epoach_time_ms = int(ts_datetime.timestamp()) * 1000
        return epoach_time_ms

    def get_messages(self, limit=None, since=None, before=None):
        """ Get raw Sigfox messages with given conditions.

        :param limit: Maximum number of messages to be read, default: None (which returns last 100 messages)
        :type limit: int, optional
        :param since: Returns messages only from this timestamp onwards. Format: "YYYY-MM-SS HH:MM:SS"
        :type since: str, optional
        :param before: Returns messages only upto this timestamp. Format: "YYYY-MM-SS HH:MM:SS"
        :type before: str, optional

        :return: List of messages
        :rtype: list
        """
        command = f"devices/{self.sigfox_id}/messages"
        parameters = {}
        if limit is not None:
            parameters["limit"] = limit
        if since is not None:
            parameters["since"] = self._get_epoach_time(since)
        if before is not None:
            parameters["before"] = self._get_epoach_time(before)
        self.logger.info("Get messages for device: %s" % self.sigfox_id)
        r_data = self.interface.get(command, parameters=parameters)
        return r_data.get("data", [])

    def is_connected(self):
        """ Checks if the connection to the Sigfox device still on

        :return: True if connected, False otherwise
        :rtype: bool
        """
        return self.interface.connected

    def measure_current(self, measure_period):
        """ Connects with the PPK2 API to measure current of the connected device

        :param measure_period: Duration of current measurement (in s)
        :type measure_period: int
        :return: status if measurement completed succesfully
        :rtype: bool
        """
        measure_status = current_measure_ppk2(measure_period)
        self.current_output_filename = "output_ppk2.csv"
        return measure_status

    def detect_current_state(self, current_state, current_output_filename="output_ppk2.csv"):
        """ Evaluate the specified state against the current measurement graph

        :param current_state: Name of the state to detect (from test_config)
        :type current_state: str
        :param current_output_filename: current measurement file to use, defaults to "output_ppk2.csv"
        :type current_output_filename: str, optional
        :return: detection status, returns True if the output table is generated normally
        :rtype: bool
        """
        current_detector = CurrentDetector(current_state, current_output_filename)
        current_detector.run_current_detector()
        states = current_detector.get_states()

        if states.empty:
            return False
        else:
            self.current_states = pd.concat([self.current_states, states], ignore_index=True)

        return True

    def get_detected_states(self):
        """ Returns the detected current states

        :return: detected states from the "detect_current_state()" method
        :rtype: pandas.DataFrame()
        """
        return self.current_states

    def plot_current_graph(self, states, file_index, folder_name, current_output_filename="output_ppk2.csv"):
        """ Plots the raw current graph from the measurement and the detected states labelled

        :param states: current states to plot on graph
        :type states: pandas.DataFrame()
        :param file_index: assigns the graph to the corresponding test case
        :type file_index: int
        :param current_output_filename: current measurement file to use, defaults to "output_ppk2.csv"
        :type current_output_filename: str, optional
        """
        current_plot = CurrentGraphPlotter(states, current_output_filename, file_index, folder_name)
        current_plot.plot_graph_with_labelled_states()


if __name__ == "__main__":
    # Example run
    DEV = SigfoxDevice("26973B7")
    DEV.connect()
    # print (DEV.get_device_info())
    messages = DEV.get_messages(limit=10, since="2022-09-08 03:46:46", before="2022-09-10 23:59:59")
    # print (messages)
    DEV.disconnect()
