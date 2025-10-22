"""Standalone script to run BLE DTM tests on Nordic NRF devices.

Purpose is to use it's buit in BLE capabilities to perform relevant tests. All current DUTs based on NRF devices are supported.
"""

from time import sleep
from itertools import chain
import logging
from typing import List, Optional

from NSTAX.equipment.NRF52XXXDK import NRF52XXXDK, dtm_constants
from NSTAX.reports.report_engine import ReportEngine

PKT_INTERVAL_US = 526  # Packet interval in microseconds (typical for BLE DTM)

class Standalone_NRF_BLE_DTM_PER_Test:
    """Runs BLE PER tests with Nordic NRF devices.

    Pre-conditions:
        - 1x NRF device loaded with DTM firmware, treated as DUT (TX)
        - 1x NRF device loaded with DTM formware, treated as test equipment (RX)
    """
    def __init__(
        self,
        tx_serial: str,
        rx_serial: str,
        phy: int,
        pkt_length: int,
        pkt_type: int,
        test_duration_s: int
    ):
        """Initialize the test with given parameters.
        :param tx_serial: COM port for the TX device
        :type tx_serial: str
        :param rx_serial: COM port for the RX device
        :type rx_serial: str
        :param phy: PHY to use (dtm_constants.PHY_1M, dtm_constants.PHY_2M, dtm_constants.PHY_S8, dtm_constants.PHY_S2)
        :type phy: int
        :param pkt_length: Packet length (0-255)
        :type pkt_length: int
        :param pkt_type: Packet type (dtm_constants.PKT_PRBS9, dtm_constants.PKT_0F, dtm_constants.PKT_55, dtm_constants.PKT_VS_FF)
        :type pkt_type: int
        :param test_duration_s: Duration of the test in seconds
        :type test_duration_s: int
        """
        self.tx_device = NRF52XXXDK(tx_serial)
        self.rx_device = NRF52XXXDK(rx_serial)
        self.phy = phy
        self.pkt_length = pkt_length
        self.pkt_type = pkt_type
        self.test_duration_s = test_duration_s
        # Define all channels in this order: 37, 0-10, 38, 11-36, 39
        self.all_channels = list(chain(range(37, 38), range(0, 11), range(38, 39), range(11, 37), range(39, 40)))
        self.results = []

    def __enter__(self):
        self.setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.teardown()

    def setup(self):
        """Setup the devices for the test."""
        try:
            self.tx_device.connect()
            self.rx_device.connect()
        except Exception as e:
            logging.error(f"Failed to connect to devices: {e}")
            raise

    def run_dtm_per_test_single_channel(self, ble_channel: int):
        """Run the BLE DTM test.

        :param ble_channel: BLE channel to test (0-39)
        :type ble_channel: int
        """
        TXD = self.tx_device
        RXD = self.rx_device

        # Setup TX device
        TXD.dtm_reset()
        TXD.dtm_set_phy(self.phy)  # Set PHY

        # Setup RX device
        RXD.dtm_reset()
        RXD.dtm_set_phy(self.phy)  # Set PHY

        # Start RX
        RXD.dtm_start_rx(channel=ble_channel, length=self.pkt_length, pkt_type=self.pkt_type)

        # Start TX
        TXD.dtm_start_tx(channel=ble_channel, length=self.pkt_length, pkt_type=self.pkt_type)

        # Wait for the test duration
        sleep(self.test_duration_s)

        # Stop TX
        TXD.dtm_stop_tx()
    
        # Stop RX and get statistics
        packets_received = RXD.dtm_stop_return_rx_packets()
        # print (f"Channel: {ble_channel}, RX Statistics: {packets_received}")

        # Calculate number of packets sent
        packets_sent = self._calculate_n_packets_sent(
            test_duration_s=self.test_duration_s,
            pkt_interval_us=PKT_INTERVAL_US
        )

        # Calculate PER
        per = self._calculate_per(packets_received=packets_received, packets_sent=packets_sent)
        per_p = round((per * 100.0), 2)

        # Store results
        self.results.append({
            "ble_channel": ble_channel,
            "phy": self.phy,
            "pkt_length": self.pkt_length,
            "pkt_type": self.pkt_type,
            "test_duration_s": self.test_duration_s,
            "packets_sent": packets_sent,
            "packets_received": packets_received,
            "per": per_p
        })

    def run_dtm_per_test_multiple_channels(self, channels: Optional[List[int]] = None):
        """Run the BLE DTM test on multiple channels.

        :param channels: List of BLE channels to test (0-39), defaults to None which means all channels
        :type channels: list, optional
        """
        if not channels:
            channels = self.all_channels
        for channel in channels:
            self.run_dtm_per_test_single_channel(channel)

    def _calculate_n_packets_sent(self, test_duration_s, pkt_interval_us):
        """Calculate number of packets sent based on test duration and packet interval.

                :param test_duration_s: Duration of the test in seconds
        :type test_duration_s: int
        :param pkt_interval_us: Packet interval in microseconds
        :type pkt_interval_us: int

        :return: Number of packets sent
        :rtype: int
        """
        if pkt_interval_us <= 0:
            raise ValueError("Packet interval must be greater than 0")
        return int(test_duration_s * 1000000 / pkt_interval_us)

    def _calculate_per(self, packets_received, packets_sent):
        """Calculate Packet Error Rate (PER).
        :param packets_received: Number of packets received
        :type packets_received: int
        :param packets_sent: Number of packets sent
        :type packets_sent: int

        :return: Packet Error Rate (PER)
        :rtype: float
        """
        try:
            per = (packets_sent - packets_received) / packets_sent
        except ZeroDivisionError:
            per = 0.0
        return per

    def teardown(self):
        """Teardown the devices after the test."""
        try:
            if self.tx_device:
                self.tx_device.disconnect()
        except Exception as e:
            logging.warning(f"Error disconnecting TX device: {e}")
        try:
            if self.rx_device:
                self.rx_device.disconnect()
        except Exception as e:
            logging.warning(f"Error disconnecting RX device: {e}")

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
        results = self.results
        report_engine_html = ReportEngine(results, template_directory, template_filename, report_filename)
        report_engine_html.create_report_html()


if __name__ == "__main__":
    """
    Example usage: Runs BLE DTM PER test and generates an HTML report.
    """
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    # Example run

    # Define test parameters    
    TX_COM = "COM7"  # COM port for the TX device
    RX_COM = "COM5"  # COM port for the RX device
    BLE_CHANNELS = []  # BLE channel to test (0-39), [] means all channels
    PHY = dtm_constants.PHY_1M  # PHY to use (dtm_constants.PHY_1M, dtm_constants.PHY_2M, dtm_constants.PHY_S8, dtm_constants.PHY_S2)
    PACKET_LENGTH = 37  # Packet length (0-255)
    PACKET_TYPE = dtm_constants.PKT_PRBS9  # Packet type (dtm_constants.PKT_PRBS9, dtm_constants.PKT_0F, dtm_constants.PKT_55, dtm_constants.PKT_VS_FF)
    TEST_DURATION_S = 5  # Duration of the test in seconds

    # Run the test
    logging.info("Starting BLE DTM PER Test...")
    with Standalone_NRF_BLE_DTM_PER_Test(TX_COM, RX_COM, PHY, PACKET_LENGTH, PACKET_TYPE, TEST_DURATION_S) as test:
        expected_runtime = len(BLE_CHANNELS) * test.test_duration_s if BLE_CHANNELS else 40 * test.test_duration_s
        logging.info(f"Running test on channels: {BLE_CHANNELS if BLE_CHANNELS else 'all channels'}, expected runtime: ~{expected_runtime} seconds")
        test.run_dtm_per_test_multiple_channels(channels=BLE_CHANNELS)

        # Create Report
        TEMPLATE_DIRECTORY = "C:/UserData/dev/NSTA/standalone_scripts/nrf_ble_dtm_test"
        TEMPLATE_FILENAME = "report_template_dtm_per.html"
        REPORT_FILENAME = "C:/UserData/dev/NSTA/standalone_scripts/nrf_ble_dtm_test/report_.html"
        test.generate_html_report(TEMPLATE_DIRECTORY, TEMPLATE_FILENAME, REPORT_FILENAME)
    logging.info("Test completed.")
