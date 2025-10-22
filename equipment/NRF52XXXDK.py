"""Equipment driver for the Nordic Semiconductor NRF 52XXX series DK or Dongles.

Purpose is to use it's buit in BLE capabilities to perform relevant tests.
"""

from time import sleep
import serial

from NSTAX.equipment.equipment import Equipment
from NSTAX.interface.rs232_interface import RS232Interface


class dtm_constants:
    """Direct Test Mode (DTM) constants as per specification."""
    # Command codes (bits 15..14)
    CMD_SETUP = 0b00
    CMD_RX    = 0b01
    CMD_TX    = 0b10
    CMD_END   = 0b11

    # Packet types (bits 7..6 of 2nd byte for RX/TX commands)
    PKT_PRBS9 = 0b00
    PKT_0F    = 0b01  # 11110000
    PKT_55    = 0b10  # 10101010
    PKT_VS_FF = 0b11  # VS on Uncoded, 0xFF on Coded

    # Test Setup "Control" codes (first byte lower 6 bits when CMD=SETUP)
    TS_RESET      = 0x00  # Parameter 0x00..0x03 => reset state to defaults
    TS_LEN_MSB    = 0x01  # set upper 2 length bits (extended length)
    TS_PHY        = 0x02  # set PHY (param selects 1M/2M/Coded S=8/S=2)
    TS_RX_MI      = 0x03  # receiver modulation index expectation
    TS_READ_FEATS = 0x04  # query supported features (optional)
    TS_TX_POWER   = 0x09  # set TX power (dBm) (optional)

    # TS_PHY parameters (choose any value in each range)
    PHY_1M = 0x04
    PHY_2M = 0x08
    PHY_S8 = 0x0C
    PHY_S2 = 0x10


class NRF52XXXDK(Equipment):
    """Equipment class for NRF52 series DK.

    :param port: COM port for the UART interface
    :type port: str
    """
    def __init__(self, port):
        super().__init__("NRF52XXXDK", version=0.1)
        self.port = port        # COM port for the DK
        self.interface = None

    # ---- Helpers to build DTM frames --------------------------------------------
    def _dtm_build_setup(self, control: int, param: int) -> bytes:
        # CMD=00, b0: [15..14]=00, [13..8]=control(6b); b1: param(8b)
        b0 = ((dtm_constants.CMD_SETUP & 0x3) << 6) | (control & 0x3F)
        b1 = param & 0xFF
        return bytes([b0, b1])

    def _dtm_build_rx(self, channel: int, length: int, pkt_type: int) -> bytes:
        # CMD=01, b0: [15..14]=01, [13..8]=channel(6b); b1: [7..6]=pkt(2b), [5..0]=len(6b)
        b0 = ((dtm_constants.CMD_RX & 0x3) << 6) | (channel & 0x3F)
        b1 = ((pkt_type & 0x3) << 6) | (length & 0x3F)
        return bytes([b0, b1])

    def _dtm_build_tx(self, channel: int, length: int, pkt_type: int) -> bytes:
        # CMD=10, same field layout as RX
        b0 = ((dtm_constants.CMD_TX & 0x3) << 6) | (channel & 0x3F)
        b1 = ((pkt_type & 0x3) << 6) | (length & 0x3F)
        return bytes([b0, b1])

    def _dtm_build_end(self) -> bytes:
        # CMD=11, control/param are 0
        b0 = ((dtm_constants.CMD_END & 0x3) << 6)
        b1 = 0x00
        return bytes([b0, b1])

    def connect(self) -> None:
        """Connect to the DK."""
        if self.is_connected():
            self.disconnect()
        self.interface = RS232Interface(self.port, baudrate=19200, EOL=None, bin_cmd=True, timeout=0.5)
        # Try to connect
        try:
            self.interface.connect()
        except self.interface.CouldNotConnectError as err:
            raise self.CouldNotConnectError(
                f"Error connecting to RS232 interface via port: {self.port}, baudrate: 19200",
                orig_error_msg=str(err)
            )
        self.connected = True

    def dtm_reset(self):
        """Reset the DTM state machine to defaults."""
        cmd = self._dtm_build_setup(dtm_constants.TS_RESET, 0x00)
        self.interface.communicate_data(cmd, strip_tx=False)
        sleep(0.1)  # Wait a bit for the reset to take effect

    def dtm_set_phy(self, phy):
        """Set the PHY for subsequent TX/RX tests.

        :param phy: One of dtm_constants.PHY_1M, PHY_2M, PHY_S8, PHY_S2
        :type phy: int
        """
        if phy not in (dtm_constants.PHY_1M, dtm_constants.PHY_2M, dtm_constants.PHY_S8, dtm_constants.PHY_S2):
            raise ValueError("Invalid PHY value, must be one of dtm_constants.PHY_1M, PHY_2M, PHY_S8, PHY_S2")
        cmd = self._dtm_build_setup(dtm_constants.TS_PHY, phy)
        self.interface.communicate_data(cmd)
        sleep(0.1)  # Wait a bit for the setting to take effect

    def dtm_start_rx(self, channel, length, pkt_type):
        """Start a RX test.

        :param channel: RF channel (0-39)
        :type channel: int
        :param length: Length of payload (0-37 bytes)
        :type length: int
        :param pkt_type: One of dtm_constants.PKT_*
        :type pkt_type: int
        """
        if not (0 <= channel <= 39):
            raise ValueError("Invalid channel, must be in range 0-39")
        if not (0 <= length <= 37):
            raise ValueError("Invalid length, must be in range 0-37")
        if pkt_type not in (dtm_constants.PKT_PRBS9, dtm_constants.PKT_0F, dtm_constants.PKT_55, dtm_constants.PKT_VS_FF):
            raise ValueError("Invalid packet type, must be one of dtm_constants.PKT_*")
        cmd = self._dtm_build_rx(channel, length, pkt_type)
        self.interface.communicate_data(cmd)
        sleep(0.1)  # Wait a bit for the RX to start

    def dtm_start_tx(self, channel, length, pkt_type):
        """Start a TX test.

        :param channel: RF channel (0-39)
        :type channel: int
        :param length: Length of payload (0-37 bytes)
        :type length: int
        :param pkt_type: One of dtm_constants.PKT_*
        :type pkt_type: int
        """
        if not (0 <= channel <= 39):
            raise ValueError("Invalid channel, must be in range 0-39")
        if not (0 <= length <= 37):
            raise ValueError("Invalid length, must be in range 0-37")
        if pkt_type not in (dtm_constants.PKT_PRBS9, dtm_constants.PKT_0F, dtm_constants.PKT_55, dtm_constants.PKT_VS_FF):
            raise ValueError("Invalid packet type, must be one of dtm_constants.PKT_*")
        cmd = self._dtm_build_tx(channel, length, pkt_type)
        self.interface.communicate_data(cmd)
        sleep(0.1)  # Wait a bit for the RX to start

    def dtm_stop_tx(self) -> None:
        """Stop the ongoing TX test."""
        cmd = self._dtm_build_end()
        resp = self.interface.communicate_data(cmd)
        if len(resp) < 2:
            raise RuntimeError("Invalid response length from DTM END command")
        # Response is 2 bytes: b0: [15..14]=11, [13..0]=num_packets(14b); b1: num_errors(8b)

    def dtm_stop_return_rx_packets(self) -> int:
        """Stop the ongoing RX test and get results.

        :return: num_packets
        :rtype: int
        """
        cmd = self._dtm_build_end()
        resp = self.interface.communicate_data(cmd)
        if len(resp) < 2:
            raise RuntimeError("Invalid response length from DTM END command")
        b0, b1 = resp[0], resp[1]
        ev = (b0 << 8) | b1
        if (ev & 0x8000):
            packets = ev & 0x7FFF
        else:
            raise ValueError("DTM END response missing expected event bit")
        return packets

    def disconnect(self):
        """Disconnect from the DK."""
        if self.is_connected():
            self.interface.disconnect()
            self.connected = False
            self.interface = None


if __name__ == "__main__":
    # Example run
    DUT = NRF52XXXDK("COM7")   # Connect to the serial port at COM7
    DUT.connect()
    DUT.dtm_reset()
    DUT.dtm_set_phy(dtm_constants.PHY_1M)  # Set PHY to 1M

    DK = NRF52XXXDK("COM5")   # Connect to the serial port at COM7
    DK.connect()            # Connect to the interface
    DK.dtm_reset()         # Reset the DTM state machine
    DK.dtm_set_phy(dtm_constants.PHY_1M)  # Set PHY to 1M

    DK.dtm_start_rx(channel=17, length=37, pkt_type=dtm_constants.PKT_PRBS9)  # Start RX on channel 20, max length, PRBS9
    sleep(0.5)
    DUT.dtm_start_tx(channel=17, length=37, pkt_type=dtm_constants.PKT_PRBS9)
    sleep(5)
    DUT.dtm_stop_tx()
    sleep(0.5)
    packets = DK.dtm_stop_return_rx_packets()         # Stop RX test and get results
    DK.disconnect()         # Free the COM port
    print(f"Done. #RX_Packets: {packets}")
