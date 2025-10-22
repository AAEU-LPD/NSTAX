"""Uplink payload decoder for Lykaner-like platform devices.

This module is to be used for verification of UL messages on demand.
"""


import datetime
import textwrap
import sys


class PlatformMessage:
    """
    Represents a Platform Message.

    :param raw_message: Raw Platform message
    :type raw_message: str
    """
    def __init__(self, raw_message_hex):
        raw_message_hex = raw_message_hex.strip()
        raw_message = self._convert_bin_str(raw_message_hex.strip())
        self.MESSAGE_HEX = raw_message_hex
        self.MESSAGE_BIN = raw_message
        if len(raw_message_hex) <= 24:
            # UL V1: Legacy SF Devices
            self.PAYLOAD = raw_message
            self.PAYLOAD_HEX = raw_message_hex
            self.DISPATCH = 0   # Represents legacy SF messages
        else:
            # UL V2: Lykaner N5 Uplink
            self.DISPATCH = self._get_dispatch(raw_message)
            header_length_bytes = 0
            if self.DISPATCH == 1:
                # Extended Lykaner uplink protocol (With Cell ID)
                service_header_bytes = 20
            elif self.DISPATCH in (2, 3,):
                # Lykaner uplink protocol payload + diagnostics
                service_header_bytes = 12
            self.SERVICE_HEADER_BIN = raw_message[:8*service_header_bytes]
            self.SERVICE_HEADER_HEX = raw_message_hex[:2*service_header_bytes]
            self.PAYLOAD = raw_message[8*service_header_bytes:]
            self.PAYLOAD_HEX = hex(int(self.PAYLOAD, 2))
            self._decode_service_header(self.SERVICE_HEADER_BIN)
        self.PAYLOAD_DECODED = self._get_payload_message_instance(self.PAYLOAD)
        self.MESSAGE_DICT = self._dict_pack()

    def _get_dispatch(self, raw_message):
        return int(raw_message[8*0+0: 8*0+8], 2)

    def _decode_service_header(self, raw_message):
        # self.DISPATCH = int(raw_message[8*0+0: 8*0+8], 2)
        self.DI_ACK = int(raw_message[8*1+6: 8*1+7], 2)
        self.DI = int(raw_message[8*1+7: 8*1+8], 2)
        timestamp_ = raw_message[8*4+0: 8*4+8]
        timestamp_ += raw_message[8*5+0: 8*5+8]
        timestamp_ += raw_message[8*6+0: 8*6+8]
        timestamp_ += raw_message[8*7+0: 8*7+8]
        timestamp_ = int(timestamp_, 2)
        self.TIMESTAMP = datetime.datetime.utcfromtimestamp(946684800 + timestamp_)
        self.LOGIC_SN = raw_message[8*8+0: 8*8+8]
        self.LOGIC_SN += raw_message[8*9+0: 8*9+8]
        self.LOGIC_SN = int(self.LOGIC_SN, 2)
        self.DI_ACK_SN = int(raw_message[8*10+0: 8*10+2], 2)
        self.DI_MSG_ID = int(raw_message[8*10+2: 8*10+8], 2)
        if self.DISPATCH == 1:
            self.NET_LOC_VALID = int(raw_message[8*1+5: 8*1+6], 2)
            self.MOBILE_NETWORK_CODE = int(raw_message[8*11+0: 8*11+8] + raw_message[8*12+0: 8*12+2], 2)
            self.MOBILE_COUNTRY_CODE = int(raw_message[8*12+2: 8*12+8] + raw_message[8*13+0: 8*13+4], 2)
            self.LOCATION_AREA_CODE = int(raw_message[8*14+0: 8*14+8] + raw_message[8*15+0: 8*15+8], 2)
            self.CELL_ID = int(raw_message[8*16+0: 8*16+8] + raw_message[8*17+0: 8*17+8] + raw_message[8*18+0: 8*18+8] + raw_message[8*19+0: 8*19+8], 2)

    def _convert_bin_str(self, hex_payload):
        """
        Converts hex payload to binary stream.

        :param raw_message: Raw SF message
        :type raw_message: str

        :return: Binary payload string
        :rtype: str
        """
        bin_payload = ""
        if hex_payload:
            for nibble_s in hex_payload:
                bin_payload += format(int(nibble_s, 16), "04b")
        return bin_payload

    def _read_type(self, raw_message):
        return int((raw_message[7] + raw_message[2:5]), 2)

    def _get_payload_message_instance(self, raw_message):
        """Gets message string and returns the relevant message instance

        :param raw_message: Raw SF like message
        :type raw_message: str

        :return: Correct message instance
        :rtype: Any, None
        """
        message_instance = None
        if self.DISPATCH in (0, 1, 2):
            if len(raw_message) == 96:
                # 12 bytes SF AP Messages
                message_instance = LykAPMessageSF(raw_message)
            else:
                message_type = self._read_type(raw_message)
                if message_type == 0x0:
                    message_instance = LykNormalStatusMessage(raw_message)
                elif message_type == 0x1:
                    message_instance = LykActivationMessage(raw_message)
                elif message_type == 0x3:
                    message_instance = LykPeriodicDiagnosticMessage(raw_message)
                elif message_type == 0x4:
                    message_instance = LykTestMessage(raw_message)
                elif message_type == 0x5:
                    message_instance = LykDownlinkRequestMessage(raw_message)
                elif message_type == 0x6:
                    message_instance = LykDownlinkACKMessage(raw_message)
                elif message_type == 0x7:
                    message_instance = LykDIStatusMessage(raw_message)
                elif message_type == 0x8:
                    message_instance = LykTransitStatusMessage(raw_message)
                elif message_type == 0x9:
                    message_instance = LykDataMessage(raw_message)
                elif message_type == 0xD:
                    message_instance = LykFunctionSpecificFrames(raw_message)
                elif message_type in (0x2, 0x04, 0x07, 0x09, 0x0A, 0x0C, 0x0F,):
                    message_instance = LykReservedMessage(raw_message)
                else:
                    message_instance = LykUnknownMessage(raw_message)
        else:
            message_instance = LykUnknownMessage(raw_message)
        return message_instance

    def __repr__(self):
        repr_ = f"Raw Payload: 0x{self.MESSAGE_HEX}\n"
        if self.DISPATCH != 0:
            if self.DISPATCH == 1:
                repr_ += f"Payload Type: Extended Lykaner uplink protocol\n"
            elif self.DISPATCH == 2:
                repr_ += f"Payload Type: Lykaner uplink protocol payload\n"
            if self.DISPATCH == 3:
                repr_ += f"Payload Type: NB-IoT diagnostic protocol\n"
            repr_ += f"Service Header: 0x{self.SERVICE_HEADER_HEX}\n"
            repr_ += f"  Dispatch: {self.DISPATCH}\n"
            if self.DISPATCH == 1:
                repr_ += f"  Net. Loc. Valid: {self.NET_LOC_VALID}\n"
            repr_ += f"  DI_ACK: {self.DI_ACK}\n" \
                    f"  DI: {self.DI}\n" \
                    f"  Timestamp: {self.TIMESTAMP}\n" \
                    f"  Logic Sequence Number: {self.LOGIC_SN}\n" \
                    f"  DI Ack Sequence number: {self.DI_ACK_SN}\n" \
                    f"  DI Message ID: {self.DI_MSG_ID}\n"
            if self.DISPATCH == 1:        
                repr_ += f"  Mobile Network Code: {self.MOBILE_NETWORK_CODE}\n" \
                    f"  Mobile Country Code: {self.MOBILE_COUNTRY_CODE}\n" \
                    f"  Location Area Code: {self.LOCATION_AREA_CODE}\n" \
                    f"  Cell ID: {self.CELL_ID}\n"
            repr_ +=  f"Payload: {self.PAYLOAD_HEX}\n"
        else:
            repr_ += f"Payload Type: Sigfox Legacy (12 Bytes Max)\n"
        repr_ += str(self.PAYLOAD_DECODED)
        return repr_

    def _dict_pack(self):
        # Convert _repr_ output to dict, experimental
        dict_op = {}
        str_op = str(self)
        for line_item in str_op.split("\n"):
            if line_item:
                key_, val_ = line_item.split(":", 1)
                dict_op[key_.strip()] = val_.strip()
        return dict_op


class LykSFMessageBase:
    """Base class for Lykaner Sigfox messages

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        self.raw_message = raw_message
        self._decode_general_header()

    def _decode_general_header(self):
        self.BATTERY_STATUS = int(self.raw_message[0:2], 2)
        self.MESSAGE_TYPE = int((self.raw_message[7] + self.raw_message[2:5]), 2)


class LykNormalStatusMessage(LykSFMessageBase):
    """Normal Status Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        temp_raw = int(self.raw_message[8*1+0: 8*1+8], 2)
        if temp_raw == 0xFF:
            self.TEMPERATURE = "OVERFLOW_OR_ERROR"
        else:
            self.TEMPERATURE = (temp_raw / 2) - 40
        ts_since_reloc = int(self.raw_message[8*2+0: 8*2+8], 2)
        if ts_since_reloc == 0xFE:
            self.TIMESTAMP_SINCE_RELOCATION = "OVERFLOW"
        elif ts_since_reloc == 0xFF:
            self.TIMESTAMP_SINCE_RELOCATION = "ERROR"
        else:
            self.TIMESTAMP_SINCE_RELOCATION = ts_since_reloc * 6

    def __repr__(self):
        repr_ = "  Message Type: Normal Status Message\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Temperature: {self.TEMPERATURE}\n" \
            f"  Timestamp since relocation detection: {self.TIMESTAMP_SINCE_RELOCATION}\n"
        return repr_


class LykActivationMessage(LykSFMessageBase):
    """Activation Status Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        temp_raw = int(self.raw_message[8*1+0: 8*1+8], 2)
        if temp_raw == 0xFF:
            self.TEMPERATURE = "OVERFLOW_OR_ERROR"
        else:
            self.TEMPERATURE = (temp_raw / 2) - 40

    def __repr__(self):
        repr_ = "  Message Type: Activation Status Message\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Temperature: {self.TEMPERATURE}\n"
        return repr_


class LykPeriodicDiagnosticMessage(LykSFMessageBase):
    """Internal Diagnostic Message (Periodic)

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self.DIAGNOSTIC_MESSAGE_TYPE = int(self.raw_message[8*1+0: 8*1+8], 2)
        if self.DIAGNOSTIC_MESSAGE_TYPE == 0xE0:
            self._decode_message_e0()
        elif self.DIAGNOSTIC_MESSAGE_TYPE == 0xE1:
            self._decode_message_e1()
        elif self.DIAGNOSTIC_MESSAGE_TYPE == 0xE2:
            self._decode_message_e2()

    def _decode_message_e0(self):
        # self.DIAGNOSTIC_MESSAGE_TYPE = int(self.raw_message[8*1+0: 8*1+8], 2)
        self.N_MCU_RESETS = int(self.raw_message[8*2+0: 8*2+8] + self.raw_message[8*3+0: 8*3+8], 2)
        self.N_DI_MESSAGES_SENT = int(self.raw_message[8*4+0: 8*4+8] + self.raw_message[8*5+0: 8*5+8], 2)
        self.N_TX_MESSAGES_SENT_NO_OTA = int(self.raw_message[8*6+0: 8*6+8] + self.raw_message[8*7+0: 8*7+8], 2)
        self.N_RX_MESSAGES_SENT_NO_OTA = int(self.raw_message[8*8+0: 8*8+8] + self.raw_message[8*9+0: 8*9+8], 2)
        self.N_MESSAGES_PUSHED_TO_CIOT_STACK = int(self.raw_message[8*10+0: 8*10+8] + self.raw_message[8*11+0: 8*11+8], 2)
        self.N_DATA_MESSAGES_PUSHED_TO_LPWAN_QUEUE = int(self.raw_message[8*12+0: 8*12+8] + self.raw_message[8*13+0: 8*13+8], 2)
        self.N_OTHER_MESSAGES_PUSHED_TO_LPWAN_QUEUE = int(self.raw_message[8*14+0: 8*14+8] + self.raw_message[8*15+0: 8*15+8], 2)
        self.N_RETRANSMITTED_DI_MESSAGES = int(self.raw_message[8*16+0: 8*16+8] + self.raw_message[8*17+0: 8*17+8], 2)
        self.N_DROPPED_DI_MESSAGES_DUE_TO_FULL_DI_QUEUE = int(self.raw_message[8*18+0: 8*18+8] + self.raw_message[8*19+0: 8*19+8], 2)
        self.N_DROPPED_DI_MESSAGES_DUE_TO_FULL_LPWAN_QUEUE = int(self.raw_message[8*20+0: 8*20+8] + self.raw_message[8*21+0: 8*21+8], 2)
        self.FILL_LEVEL_DI_QUEUE = int(self.raw_message[8*22+0: 8*22+8], 2)
        self.N_TX_CIOT_TRANSMISSIONS_INCLUDING_OTA = int(self.raw_message[8*23+0: 8*23+8] + self.raw_message[8*24+0: 8*24+8] + self.raw_message[8*25+0: 8*25+8], 2)
        self.N_RX_CIOT_TRANSMISSIONS_INCLUDING_OTA = int(self.raw_message[8*26+0: 8*26+8] + self.raw_message[8*27+0: 8*27+8], 2)

        self.repr_ = "  Message Type: Internal Diagnostic Message (Periodic)\n" \
            f"  Diagnostic message type: {self.DIAGNOSTIC_MESSAGE_TYPE}\n" \
            f"  Number of MCU resets: {self.N_MCU_RESETS}\n" \
            f"  Number of DI messages sent: {self.N_DI_MESSAGES_SENT}\n" \
            f"  Number of TX transmissions without OTA: {self.N_TX_MESSAGES_SENT_NO_OTA}\n" \
            f"  Number of RX transmissions without OTA: {self.N_RX_MESSAGES_SENT_NO_OTA}\n" \
            f"  Total number of messages pushed to the ciot stack: {self.N_MESSAGES_PUSHED_TO_CIOT_STACK}\n" \
            f"  Number of Data Messages pushed to the lpwan queue: {self.N_DATA_MESSAGES_PUSHED_TO_LPWAN_QUEUE}\n" \
            f"  Number of other messages pushed to the lpwan queue: {self.N_OTHER_MESSAGES_PUSHED_TO_LPWAN_QUEUE}\n" \
            f"  16 Number of retransmitted DI messages: {self.N_RETRANSMITTED_DI_MESSAGES}\n" \
            f"  Number of dropped DI messages due to full DI queue: {self.N_DROPPED_DI_MESSAGES_DUE_TO_FULL_DI_QUEUE}\n" \
            f"  Number of dropped messages due to full lpwan queue: {self.N_DROPPED_DI_MESSAGES_DUE_TO_FULL_LPWAN_QUEUE}\n" \
            f"  Fill level of DI queue: {self.FILL_LEVEL_DI_QUEUE}\n" \
            f"  Number of TX ciot transmissions including OTA: {self.N_TX_CIOT_TRANSMISSIONS_INCLUDING_OTA}\n" \
            f"  Number of RX ciot transmissions including OTA: {self.N_RX_CIOT_TRANSMISSIONS_INCLUDING_OTA}\n"

    def _decode_message_e1(self):
        # self.DIAGNOSTIC_MESSAGE_TYPE = int(self.raw_message[8*1+0: 8*1+8], 2)
        self.MAX_TEMPERATURE_IN_C_WITH_55C_OFFSET = int(self.raw_message[8*2+0: 8*2+8], 2)
        self.MIN_TEMPERATURE_IN_C_WITH_55C_OFFSET = int(self.raw_message[8*3+0: 8*3+8], 2)
        self.TEMPERATURE_PROFILE_FIRST_ENTRY = int(self.raw_message[8*4+0: 8*4+8] + self.raw_message[8*5+0: 8*5+8] + self.raw_message[8*6+0: 8*6+8] + self.raw_message[8*7+0: 8*7+8], 2)
        self.TEMPERATURE_PROFILE_SECOND_ENTRY = int(self.raw_message[8*8+0: 8*8+8] + self.raw_message[8*9+0: 8*9+8] + self.raw_message[8*10+0: 8*10+8] + self.raw_message[8*11+0: 8*11+8], 2)
        self.TEMPERATURE_PROFILE_THIRD_ENTRY = int(self.raw_message[8*12+0: 8*12+8] + self.raw_message[8*13+0: 8*13+8] + self.raw_message[8*14+0: 8*14+8] + self.raw_message[8*15+0: 8*15+8], 2)
        self.TEMPERATURE_PROFILE_FOURTH_ENTRY = int(self.raw_message[8*16+0: 8*16+8] + self.raw_message[8*17+0: 8*17+8] + self.raw_message[8*18+0: 8*18+8] + self.raw_message[8*19+0: 8*19+8], 2)
        self.TEMPERATURE_PROFILE_FIFTH_ENTRY = int(self.raw_message[8*20+0: 8*20+8] + self.raw_message[8*21+0: 8*21+8] + self.raw_message[8*22+0: 8*22+8] + self.raw_message[8*23+0: 8*23+8], 2)
        self.TEMPERATURE_PROFILE_SIXTH_ENTRY = int(self.raw_message[8*24+0: 8*24+8] + self.raw_message[8*25+0: 8*25+8] + self.raw_message[8*26+0: 8*26+8] + self.raw_message[8*27+0: 8*27+8], 2)

        self.repr_ = "  Message Type: Internal Diagnostic Message (Periodic)\n" \
            f"  Diagnostic message type: {self.DIAGNOSTIC_MESSAGE_TYPE}\n" \
            f"  Max Temperature in C with +55C offset: {self.MAX_TEMPERATURE_IN_C_WITH_55C_OFFSET}\n" \
            f"  Min Temperature in C with +55C offset: {self.MIN_TEMPERATURE_IN_C_WITH_55C_OFFSET}\n" \
            f"  Temperature Profile First Entry: {self.TEMPERATURE_PROFILE_FIRST_ENTRY}\n" \
            f"  Temperature Profile Second Entry: {self.TEMPERATURE_PROFILE_SECOND_ENTRY}\n" \
            f"  Temperature Profile Third Entry: {self.TEMPERATURE_PROFILE_THIRD_ENTRY}\n" \
            f"  Temperature Profile Fourth Entry: {self.TEMPERATURE_PROFILE_FOURTH_ENTRY}\n" \
            f"  Temperature Profile Fifth Entry: {self.TEMPERATURE_PROFILE_FIFTH_ENTRY}\n" \
            f"  Temperature Profile Sixth Entry: {self.TEMPERATURE_PROFILE_SIXTH_ENTRY}\n"

    def _decode_message_e2(self):
        # self.DIAGNOSTIC_MESSAGE_TYPE = int(self.raw_message[8*1+0: 8*1+8], 2)
        self.TEMPERATURE_PROFILE_SEVENTH_ENTRY = int(self.raw_message[8*2+0: 8*2+8] + self.raw_message[8*3+0: 8*3+8] + self.raw_message[8*4+0: 8*4+8] + self.raw_message[8*5+0: 8*5+8], 2)
        self.TEMPERATURE_PROFILE_EIGHTH_ENTRY = int(self.raw_message[8*6+0: 8*6+8] + self.raw_message[8*7+0: 8*7+8] + self.raw_message[8*8+0: 8*8+8] + self.raw_message[8*9+0: 8*9+8], 2)
        self.TOTAL_ESTIMATED_BATTERY_CAPACITY_MAH = int(self.raw_message[8*10+0: 8*10+8] + self.raw_message[8*11+0: 8*11+8] + self.raw_message[8*12+0: 8*12+8], 2)
        self.TOTAL_CONSUMED_BATTERY_CAPACITY_MAH = int(self.raw_message[8*13+0: 8*13+8] + self.raw_message[8*14+0: 8*14+8] + self.raw_message[8*15+0: 8*15+8], 2)
        self.N_IWDG_RESETS = int(self.raw_message[8*16+0: 8*16+8] + self.raw_message[8*17+0: 8*17+8], 2)
        self.N_POWER_RESETS = int(self.raw_message[8*18+0: 8*18+8] + self.raw_message[8*19+0: 8*19+8], 2)
        self.N_FULL_RELOCATION_CYCLES = int(self.raw_message[8*20+0: 8*20+8] + self.raw_message[8*21+0: 8*21+8], 2)
        self.N_FALSE_POSITIVE_MOTION_CYCLES = int(self.raw_message[8*22+0: 8*22+8] + self.raw_message[8*23+0: 8*23+8], 2)
        self.OVERALL_TIME_FALSELY_IN_TRUMI_STATE = int(self.raw_message[8*24+0: 8*24+8] + self.raw_message[8*25+0: 8*25+8] + self.raw_message[8*26+0: 8*26+8], 2)
        self.RESERVED = self.raw_message[8*27+0: 8*27+8]

        self.repr_ = "  Message Type: Internal Diagnostic Message (Periodic)\n" \
            f"  Temperature Profile Seventh Entry: {self.TEMPERATURE_PROFILE_SEVENTH_ENTRY}\n" \
            f"  Temperature Profile Eighth Entry: {self.TEMPERATURE_PROFILE_EIGHTH_ENTRY}\n" \
            f"  Total estimated battery capacity in mAh: {self.TOTAL_ESTIMATED_BATTERY_CAPACITY_MAH}\n" \
            f"  Total consumed battery capacity in mAh: {self.TOTAL_CONSUMED_BATTERY_CAPACITY_MAH}\n" \
            f"  Number of IWDG resets: {self.N_IWDG_RESETS}\n" \
            f"  Number of power resets: {self.N_POWER_RESETS}\n" \
            f"  Number of full relocation cycles: {self.N_FULL_RELOCATION_CYCLES}\n" \
            f"  Number of false positive motion cycles: {self.N_FALSE_POSITIVE_MOTION_CYCLES}\n" \
            f"  Overall time falsely in Trumi state: {self.OVERALL_TIME_FALSELY_IN_TRUMI_STATE}\n" \
            f"  Reserved: {self.RESERVED}\n"

    def __repr__(self):
        return self.repr_


class _LykPeriodicDiagnosticMessage_Legacy(LykSFMessageBase):
    """Internal Diagnostic Message (Periodic)

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        self.DIAGNOSTIC_MESSAGE_TYPE = int(self.raw_message[8*1+0: 8*1+8], 2)
        self.MESSAGE_COUNTER = int(self.raw_message[8*2+0: 8*2+8] + self.raw_message[8*3+0: 8*3+8], 2)
        self.MAX_TEMPERATURE = int(self.raw_message[8*4+0: 8*4+8], 2)
        self.MIN_TEMPERATURE = int(self.raw_message[8*5+0: 8*5+8], 2)
        self.N_TRUMI_STATE_CHANGES = int(self.raw_message[8*6+0: 8*6+8] + self.raw_message[8*7+0: 8*7+8], 2)
        self.N_ACTIVATIONS = int(self.raw_message[8*8+0: 8*8+8], 2)
        self.N_ALARMS = int(self.raw_message[8*9+0: 8*9+8], 2)
        self.N_RESETS_LSB = int(self.raw_message[8*10+0: 8*10+8], 2)

    def __repr__(self):
        repr_ = "  Message Type: Internal Diagnostic Message (Periodic)\n" \
            f"  Diagnostic message type: {self.DIAGNOSTIC_MESSAGE_TYPE}\n" \
            f"  Message counter: {self.MESSAGE_COUNTER}\n" \
            f"  Maximum temperature: {self.MAX_TEMPERATURE}\n" \
            f"  Minimum temperature: {self.MIN_TEMPERATURE}\n" \
            f"  Number of state change TRUMI: {self.N_TRUMI_STATE_CHANGES}\n" \
            f"  Number of activations: {self.N_ACTIVATIONS}\n" \
            f"  Number of alarms: {self.N_ALARMS}\n" \
            f"  Number of resets LSB: {self.N_RESETS_LSB}\n"
        return repr_


class LykTestMessage(LykSFMessageBase):
    """Test Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        self.DIAGNOSTIC_MESSAGE_TYPE = int(self.raw_message[8*1+0: 8*1+8], 2)
        self.MESSAGE_COUNTER = int(self.raw_message[8*2+0: 8*2+8] + self.raw_message[8*3+0: 8*3+8], 2)
        self.MAX_TEMPERATURE = int(self.raw_message[8*4+0: 8*4+8], 2)
        self.MIN_TEMPERATURE = int(self.raw_message[8*5+0: 8*5+8], 2)
        self.N_TRUMI_STATE_CHANGES = int(self.raw_message[8*6+0: 8*6+8] + self.raw_message[8*7+0: 8*7+8], 2)
        self.N_ACTIVATIONS = int(self.raw_message[8*8+0: 8*8+8], 2)
        self.N_ALARMS = int(self.raw_message[8*9+0: 8*9+8], 2)
        self.N_RESETS_LSB = int(self.raw_message[8*10+0: 8*10+8], 2)

    def __repr__(self):
        repr_ = "  Message Type: Test Message\n" \
            f"  Diagnostic message type: {self.DIAGNOSTIC_MESSAGE_TYPE}\n" \
            f"  Message counter: {self.MESSAGE_COUNTER}\n" \
            f"  Maximum temperature: {self.MAX_TEMPERATURE}\n" \
            f"  Minimum temperature: {self.MIN_TEMPERATURE}\n" \
            f"  Number of state change TRUMI: {self.N_TRUMI_STATE_CHANGES}\n" \
            f"  Number of activations: {self.N_ACTIVATIONS}\n" \
            f"  Number of alarms: {self.N_ALARMS}\n" \
            f"  Number of resets LSB: {self.N_RESETS_LSB}\n"
        return repr_


class LykDownlinkRequestMessage(LykSFMessageBase):
    """DL Request Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        self.PREV_DL_RESULT = int(self.raw_message[8*1+0: 8*1+2], 2)
        self.MIRROR_CONT_DL_MSG = int(self.raw_message[8*1+2], 2)
        self.IS_REPEATED_REQ = int(self.raw_message[8*1+3], 2)
        self.SEQUENCE_NUMBER = int(self.raw_message[8*1+4: 8*1+8], 2)
        self.PATCH_VERSION = int(self.raw_message[8*2+0: 8*2+4], 2)
        self.VERSION_FORMAT = int(self.raw_message[8*2+4: 8*2+6], 2)
        self.FIRST_REQ_AFTER_STARTUP = int(self.raw_message[8*2+6], 2)
        self.IS_PENDING_REQ = int(self.raw_message[8*2+7], 2)
        self.MAJOR_VERSION = int((self.raw_message[8*4+5: 8*4+8] + self.raw_message[8*3+0: 8*3+8]), 2)
        self.MINOR_VERSION = int((self.raw_message[8*5+0: 8*5+8] + self.raw_message[8*4+0: 8*4+4]), 2)

    def __repr__(self):
        repr_ = "  Message Type: Downlink Request\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Result of applying previous downlink configuration: {self.PREV_DL_RESULT}\n" \
            f"  Mirror of continuous bit in downlink message: {self.MIRROR_CONT_DL_MSG}\n" \
            f"  Is repeated request: {self.IS_REPEATED_REQ}\n" \
            f"  Sequence number (incremented for each request if continuous bit is set): {self.SEQUENCE_NUMBER}\n" \
            f"  Patch Version: {self.PATCH_VERSION}\n" \
            f"  Version format: {self.VERSION_FORMAT}\n" \
            f"  First request after system start-up: {self.FIRST_REQ_AFTER_STARTUP}\n" \
            f"  Is pending request: {self.IS_PENDING_REQ}\n" \
            f"  Major Version: {self.MAJOR_VERSION}\n" \
            f"  Minor Version: {self.MINOR_VERSION}\n"
        return repr_


class LykDownlinkACKMessage(LykSFMessageBase):
    """DL ACK Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        self.REQUEST_PROTOCOL_VERSION = int(self.raw_message[8*1+0: 8*1+4], 2)
        app_resp = int(self.raw_message[8*1+5: 8*1+7], 2)
        self.DL_PARAM_APP_RESPONSE = {
            0: "OK",
            1: "Incorrect Type Id or downlink payload version",
            2: "Type id is locked",
            3: "Received error"
        }.get(app_resp, None)
        ack_resp = int(self.raw_message[8*1+7], 2)
        self.DL_ACK = {
            1: "POSITIVE_ACK",
            0: "NEGATIVE_ACK"
        }.get(ack_resp, None)
        self.INTERNAL_DIAG_DATA = self.raw_message[8*2+0: 8*2+8]

    def __repr__(self):
        repr_ = "  Message Type: Downlink ACK\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Request protocol version: {self.REQUEST_PROTOCOL_VERSION}\n" \
            f"  Result of applying previous downlink configuration: {self.DL_PARAM_APP_RESPONSE}\n" \
            f"  Downlink ACK: {self.DL_ACK}\n" \
            f"  Internal Diagnostics Data: {self.INTERNAL_DIAG_DATA}\n"
        return repr_


class LykDIStatusMessage(LykSFMessageBase):
    """Data Integrity Status Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        temp_raw = int(self.raw_message[8*1+0: 8*1+8], 2)
        if temp_raw == 0xFF:
            self.TEMPERATURE = "OVERFLOW_OR_ERROR"
        else:
            self.TEMPERATURE = (temp_raw / 2) - 40
        self.ACK_SEQ_NR = int(self.raw_message[8*0+5: 8*0+7], 2)

    def __repr__(self):
        repr_ = "  Message Type: Normal Status Message\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Temperature: {self.TEMPERATURE}\n" \
            f"  ACK Sequence Number: {self.ACK_SEQ_NR}\n"
        return repr_


class LykTransitStatusMessage(LykSFMessageBase):
    """Transit Status Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        temp_raw = int(self.raw_message[8*1+0: 8*1+8], 2)
        if temp_raw == 0xFF:
            self.TEMPERATURE = "ERROR"
        else:
            self.TEMPERATURE = (temp_raw / 2) - 40
        ts_since_reloc = int(self.raw_message[8*2+0: 8*2+8], 2)
        if ts_since_reloc == 0xFE:
            self.TIMESTAMP_SINCE_RELOCATION = "OVERFLOW"
        elif ts_since_reloc == 0xFF:
            self.TIMESTAMP_SINCE_RELOCATION = "ERROR"
        else:
            self.TIMESTAMP_SINCE_RELOCATION = ts_since_reloc * 6

    def __repr__(self):
        repr_ = "  Message Type: Transit Status Message\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Temperature: {self.TEMPERATURE}\n" \
            f"  Timestamp since relocation detection: {self.TIMESTAMP_SINCE_RELOCATION}\n"
        return repr_


class LykFunctionSpecificFrames(LykSFMessageBase):
    """Function Specific Frames

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self._decode_message()

    def _decode_message(self):
        self.repr_ = """"""
        self.SUB_FRAME_ID = int((self.raw_message[8*2+4: 8*2+8] + self.raw_message[8*1+0: 8*1+2]), 2)
        self.SPECIFIC_FUNCTION_ID = int(self.raw_message[8*1+2: 8*1+8], 2)
        self.SEQUENCE_NUMBER = int(self.raw_message[8*2+0: 8*2+4], 2)
        if self.SPECIFIC_FUNCTION_ID == 0x3 and self.SUB_FRAME_ID == 0x3:
            self.SPECIFIC_APPLICATION = "OTS App - Keep Alive Message Frame"
            temp_raw = int(self.raw_message[8*3+0: 8*3+8], 2)
            if temp_raw == 0xFF:
                self.TEMPERATURE = "OVERFLOW_OR_ERROR"
            else:
                self.TEMPERATURE = (temp_raw / 2) - 40
        elif self.SPECIFIC_FUNCTION_ID == 0x3 and self.SUB_FRAME_ID == 0x4:
            self.SPECIFIC_APPLICATION = "OTS App - Relocation Finished Message Frame"
            temp_raw = int(self.raw_message[8*3+0: 8*3+8], 2)
            if temp_raw == 0xFF:
                self.TEMPERATURE = "OVERFLOW_OR_ERROR"
            else:
                self.TEMPERATURE = (temp_raw / 2) - 40
            rel_time_since_reloc = int(self.raw_message[8*4+0: 8*4+8], 2)
            if rel_time_since_reloc == 0xFF:
                self.RELATIVE_TIME_SINCE_RELOCATION_STARTED = "ERROR"
            elif rel_time_since_reloc == 0xFE:
                self.RELATIVE_TIME_SINCE_RELOCATION_STARTED = "OVERFLOW"
            else:
                self.RELATIVE_TIME_SINCE_RELOCATION_STARTED = rel_time_since_reloc * 6
            rel_time_since_motion = int(self.raw_message[8*5+0: 8*5+8], 2)
            if rel_time_since_motion == 0xFF:
                self.RELATIVE_TIME_SINCE_MOTION_STARTED = "ERROR"
            elif rel_time_since_motion == 0xFE:
                self.RELATIVE_TIME_SINCE_MOTION_STARTED = "OVERFLOW"
            else:
                self.RELATIVE_TIME_SINCE_MOTION_STARTED = rel_time_since_motion * 6
        elif self.SPECIFIC_FUNCTION_ID == 0x5 and self.SUB_FRAME_ID == 0x0:
            self.SPECIFIC_APPLICATION = "Temperature Alarm Message"
            alarm_type_t = int(self.raw_message[8*3+0], 2)
            self.ALARM_TYPE = {
                1: "MAXIMUM_TEMPERATURE_THRESHOLD_CROSSED",
                0: "MINIMUM_TEMPERATURE_THRESHOLD_CROSSED"
            }.get(alarm_type_t, None)
            self.CURRENT_TEMPERATURE = int(self.raw_message[8*3+1: 8*3+8], 2) - 40
            motion_type_t = int(self.raw_message[8*4+0], 2)
            self.MOTION_TYPE = {
                1: "RELOCATION_STATE",
                0: "STORED_STATE"
            }.get(motion_type_t, None)
            self.CRITICAL_TEMPERATURE = int(self.raw_message[8*4+1: 8*4+8], 2) - 40
            rel_time_since_alarm = int(self.raw_message[8*5+0: 8*5+8], 2)
            if rel_time_since_alarm == 0xFF:
                self.RELATIVE_TIME_SINCE_ALARM_DETECTED = "OVERFLOW_OR_ERROR"
            else:
                self.RELATIVE_TIME_SINCE_ALARM_DETECTED = rel_time_since_alarm * 20
        elif self.SPECIFIC_FUNCTION_ID == 0x5 and self.SUB_FRAME_ID == 0x1:
            self.SPECIFIC_APPLICATION = "General Diagnostic – Temperature Message Frame"
            temp_raw = int(self.raw_message[8*3+0: 8*3+8], 2)
            if temp_raw == 0xFF:
                self.TEMPERATURE = "OVERFLOW_OR_ERROR"
            else:
                self.TEMPERATURE = (temp_raw / 2) - 40
            max_temp_raw = int(self.raw_message[8*4+0: 8*4+8], 2)
            if max_temp_raw == 0xFF:
                self.MAXIMUM_TEMPERATURE = "OVERFLOW_OR_ERROR"
            else:
                self.MAXIMUM_TEMPERATURE = (max_temp_raw / 2) - 40
            min_temp_raw = int(self.raw_message[8*5+0: 8*5+8], 2)
            if min_temp_raw == 0xFF:
                self.MINIMUM_TEMPERATURE = "OVERFLOW_OR_ERROR"
            else:
                self.MINIMUM_TEMPERATURE = (min_temp_raw / 2) - 40
        elif self.SPECIFIC_FUNCTION_ID == 0x0 and self.SUB_FRAME_ID == 0x0:
            self.SPECIFIC_APPLICATION = "Orientation Detection Report Frame"
            mount_type_t = int((self.raw_message[8*4+7] + self.raw_message[8*3+0: 8*3+4]), 2)
            self.DEVICE_MOUNTING_TYPE = {
                0: "Right, Front Side (SUI_RIGHT_FRONT_SIDE)",
                1: "Right, Right Side (SUI_RIGHT_RIGHT_SIDE)",
                2: "Right, Back Side (SUI_RIGHT_BACK_SIDE)",
                3: "Right, Left Side (SUI_RIGHT_LEFT_SIDE)",
                4: "Down, Front Side (SUI_DOWN_FRONT_SIDE)",
                5: "Down, Right Side (SUI_DOWN_RIGHT_SIDE)",
                6: "Down, Back Side (SUI_DOWN_BACK_SIDE)",
                7: "Down, Left Side (SUI_DOWN_FRONT_SIDE)",
                8: "Left, Front Side (SUI_LEFT_FRONT_SIDE)",
                9: "Left, Right Side (SUI_LEFT_RIGHT_SIDE)",
                10: "Left, Back Side (SUI_LEFT_BACK_SIDE)",
                11: "Left, Left Side (SUI_LEFT_LEFT_SIDE)",
                12: "Up, Front Side (SUI_UP_FRONT_SIDE)",
                13: "Up, Right Side (SUI_UP_RIGHT_SIDE)",
                14: "Up, Back Side (SUI_UP_BACK_SIDE)",
                15: "Up, Left Side (SUI_UP_LEFT_SIDE)",
                16: "Top, Front Side (SUI_TOP_FRONT_SIDE)",
                17: "Top, Right Side (SUI_TOP_RIGHT_SIDE)",
                18: "Top, Back Side (SUI_TOP_BACK_SIDE)",
                19: "Top, Left Side (SUI_TOP_LEFT_SIDE)",
                20: "Bottom, Front Side (SUI_BOTTOM_FRONT_SIDE)",
                21: "Bottom, Right Side (SUI_BOTTOM_RIGHT_SIDE)",
                22: "Bottom, Back Side (SUI_BOTTOM_BACK_SIDE)",
                23: "Bottom, Left Side (SUI_BOTTOM_LEFT_SIDE)"
            }.get(mount_type_t, None)
            orientation_state_t = int(self.raw_message[8*3+4: 8*3+8], 2)
            self.DEVICE_ORIENTATION_STATE = {
                0: "UNKNWON",
                1: "STATE 1",
                2: "STATE 2",
                3: "STATE 3",
                4: "STATE 4",
                5: "STATE 5",
                6: "STATE 6"
            }.get(orientation_state_t, None)
            internal_data_t = int((self.raw_message[8*4+0: 8*4+7] + self.raw_message[8*5+0: 8*10+8]), 2)
            self.INTERNAL_DATA = internal_data_t
        else:
            self.SPECIFIC_APPLICATION = "NOT IMPLEMENTED / UNKNOWN"
            self.FUNCTION_SPECIFIC_PAYLOAD = int(self.raw_message[8*3+0: 8*10+8], 2)

    def __repr__(self):
        repr_ = "  Message Type: Uplink Function Specific Frame\n" \
            f"  Battery Status: {self.BATTERY_STATUS}\n" \
            f"  Sub Frame ID: {self.SUB_FRAME_ID}\n" \
            f"  Specific Function ID: {self.SPECIFIC_FUNCTION_ID}\n" \
            f"  Specific Application Name: {self.SPECIFIC_APPLICATION}\n"
        if self.SPECIFIC_APPLICATION == "OTS App - Keep Alive Message Frame":
            repr_ += "    Function Specific Message Type: OTS App - Keep Alive Message Frame\n" \
                f"    Temperature: {self.TEMPERATURE}\n"
        elif self.SPECIFIC_APPLICATION == "OTS App - Relocation Finished Message Frame":
            repr_ += "    Function Specific Message Type: OTS App - Relocation Finished Message Frame\n" \
                f"    Temperature: {self.TEMPERATURE}\n" \
                f"    Timestamp since motion detection: {self.RELATIVE_TIME_SINCE_MOTION_STARTED}\n" \
                f"    Timestamp since relocation detection: {self.RELATIVE_TIME_SINCE_RELOCATION_STARTED}\n"
        elif self.SPECIFIC_APPLICATION == "Temperature Alarm Message":
            repr_ += "    Function Specific Message Type: Temperature Alarm Message\n" \
                f"    Alarm Type: {self.ALARM_TYPE}\n" \
                f"    Current Temperature: {self.CURRENT_TEMPERATURE}\n" \
                f"    Motion Type: {self.MOTION_TYPE}\n" \
                f"    Critical Temperature: {self.CRITICAL_TEMPERATURE}\n" \
                f"    Relative Time Since Alarm Detected: {self.RELATIVE_TIME_SINCE_ALARM_DETECTED}\n"
        elif self.SPECIFIC_APPLICATION == "General Diagnostic – Temperature Message Frame":
            repr_ += "    Function Specific Message Type: General Diagnostic – Temperature Message Frame\n" \
                f"    Temperature: {self.TEMPERATURE}\n" \
                f"    Maximum Temperature: {self.MAXIMUM_TEMPERATURE}\n" \
                f"    Minimum Temperature: {self.MINIMUM_TEMPERATURE}\n"
        elif self.SPECIFIC_APPLICATION == "Orientation Detection Report Frame":
            repr_ += "    Function Specific Message Type: Orientation Detection Report Frame\n" \
                f"    Device Mounting Type: {self.DEVICE_MOUNTING_TYPE}\n" \
                f"    Device Orientation State: {self.DEVICE_ORIENTATION_STATE}\n" \
                f"    Internal Data: {self.INTERNAL_DATA}\n"
        return repr_


class LykAPMessageSF:
    """Wifi AP Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        self.AP1 = self.AP2 = None
        self.TYPE_00 = self.TYPE_01 = self.TYPE_60 = self.TYPE_61 = None
        self.DI = None
        self.NORMAL_FRAME = self.KEEPALIVE_FRAME = False
        self._decode_message(raw_message)

    def _decode_message(self, raw_message):
        self.TYPE_00 = int(raw_message[0*8+7])
        self.TYPE_01 = int(raw_message[0*8+6])
        self.TYPE_60 = int(raw_message[6*8+7])
        self.TYPE_61 = int(raw_message[6*8+6])
        ap_str = raw_message
        ap_str = self._replace_char(ap_str, 0*8+7, "0")
        ap_str = self._replace_char(ap_str, 0*8+6, "0")
        ap_str = self._replace_char(ap_str, 6*8+7, "0")
        ap_str = self._replace_char(ap_str, 6*8+6, "0")
        self.AP1 = ":".join(textwrap.wrap("%012X" % int(ap_str[:48], 2), width=2))
        self.AP2 = ":".join(textwrap.wrap("%012X" % int(ap_str[48:], 2), width=2))
        if self.TYPE_00 == 1:
            self.DI = True
        else:
            self.DI = False
        if self.TYPE_60 == 1:
            self.KEEPALIVE_FRAME = True
        else:
            self.NORMAL_FRAME = True

    def _replace_char(self, string_input, replacement_index, replacement_char):
        return string_input[:replacement_index] + replacement_char + string_input[replacement_index + 1:]

    def __repr__(self):
        repr_ = "  Message Type: AP Message\n" \
            f"  AP1: {self.AP1}\n" \
            f"  AP2: {self.AP2}\n" \
            f"  TYPE_00: {self.TYPE_00}\n" \
            f"  TYPE_01: {self.TYPE_01}\n" \
            f"  TYPE_60: {self.TYPE_60}\n" \
            f"  TYPE_61: {self.TYPE_61}\n"
        return repr_


class LykDataMessage(LykSFMessageBase):
    """Wifi AP Message V2

    :param raw_message: Raw data message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)
        self.APs = []
        self._decode_message(raw_message)

    def _decode_message(self, raw_message):
        data_message_type = int(raw_message[8*1+0: 8*1+8], 2)
        if data_message_type == 1:
            self.DATA_MESSAGE_TYPE = "Wifi MAC address"
        elif data_message_type == 2:
            self.DATA_MESSAGE_TYPE = "Wifi MAC address + Cellular location data"
        else:
            self.DATA_MESSAGE_TYPE = "RESERVED"
        trigger_type = int(raw_message[8*2+0: 8*2+4], 2)
        if trigger_type == 0:
            self.TRIGGER_TYPE = "Normal (Motion Trigger)"
        elif trigger_type == 1:
            self.TRIGGER_TYPE = "Keep Alive (Time trigger)"
        elif trigger_type == 2:
            self.TRIGGER_TYPE = "Orientation Detection"
        else:
            self.TRIGGER_TYPE = "Reserved"
        self.MAC_COUNT = int(raw_message[8*2+4: 8*2+8], 2)
        bssids_string = raw_message[8*3:]
        bssids_bin = [bssids_string[i:i+48] for i in range(0, len(bssids_string), 48)]
        for bssid_ in bssids_bin:
            self.APs.append(":".join(textwrap.wrap("%012X" % (int(bssid_, 2)), width=2)))
    
    def __repr__(self):
        repr_ = "  Message Type: Data Message\n"
        repr_ += f"  Data Message Type: {self.DATA_MESSAGE_TYPE}\n" \
                f"  Trigger Type: {self.TRIGGER_TYPE}\n" \
                f"  MAC Count: {self.MAC_COUNT}\n"
        for id_, ap_ in enumerate(self.APs, start=1):
            repr_ += f"  MAC{id_}: {ap_}\n"
        return repr_


class LykUnknownMessage(LykSFMessageBase):
    """Unknown / Undecodable / Unimplemented Message

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)

    def __repr__(self):
        repr_ = "  Message Type: Unknown / Undecodable / Unimplemented Message\n"
        repr_ += f"  Payload (bin): {self.raw_message}\n"
        return repr_


class LykReservedMessage(LykSFMessageBase):
    """Reserved Messages

    :param raw_message: Raw SF message
    :type raw_message: str
    """
    def __init__(self, raw_message):
        super().__init__(raw_message)

    def __repr__(self):
        repr_ = "  Message Type: Reserved Message\n"
        repr_ += f"  Payload (bin): {self.raw_message}\n"
        return repr_


if __name__ == "__main__":

    # MSG = PlatformMessage("020000002bf12c5200000000c880")   # Activation example
    # print (MSG)

    # Main founction
    import argparse
    parser = argparse.ArgumentParser(description="Lykaner Uplink Message Decoder")
    parser.add_argument("-m", "--message", help="Payload in hex", required=False)
    parser.add_argument("-i", help="Iterative Inputs", action="store_true")
    parser.add_argument("-f", help="Enter CSV Path With Multiple Payloads", required=False)
    args = vars(parser.parse_args())
    #args = parser.parse_args(args=None if sys.argv[1:] else ['--help'])

    if args["message"]:
        MSG = PlatformMessage(args["message"])
        print (MSG)
    elif args["i"]:
        while True:
            payload = input("Enter HEX Payload (q to quit): ").strip()
            if payload in ("q", "Q"):
                break
            MSG = PlatformMessage(payload)
            print ("==================================================")
            print (MSG)
    elif args["f"]:
        with open(args["f"]) as csv_file:
            payloads = csv_file.read().split(",")
            for payload in payloads:
                MSG = PlatformMessage(payload)
                print ("==================================================")
                print (MSG)

    ####### Example payloads UL v1 #######
    # MSG = PlatformMessage("c887")                           # Activation
    # MSG = PlatformMessage("b0b86718f6c2b1b86718f6c3")       # AP: Time Triggered
    # MSG = PlatformMessage("ccd42e1a8d30ccd42e25cbea")       # AP: Motion Triggered
    # MSG = PlatformMessage("c07102")                         # Normal Status Message
    # MSG = PlatformMessage("e8000e15200010")                 # DL Request
    # MSG = PlatformMessage("f04600")                         # DL ACK
    # MSG = PlatformMessage("342792ae3ff07d7716ed4bd1")       # Test Message
    # MSG = PlatformMessage("d834568909121212121212")         # Dummy Periodic Diag Message
    # MSG = PlatformMessage("020000002c1307b400000000c87c")   # Boot
    # MSG = PlatformMessage("020000002c1307b400000000c87c")   # Boot
    # MSG = PlatformMessage("e0d000001e1e0000000001")   # Test Message

    ####### Example payloads UL v2 #######
    # MSG = PlatformMessage("020000002c13083200020000e8000f17200094")   # DL Request
    # MSG = PlatformMessage("020000002c13084600030000f04100")   # DL ACK
    # MSG = PlatformMessage("020000002bf12c5200000000c880")   # Activation
    # MSG = PlatformMessage("020000002bf12c5800010000c90133b0b86718f6c3b0b86718f6c23817c37f9703")   # DL Request
    # MSG = PlatformMessage("020100002c25972100650e00c90123b0b8671945e2b0b8671945e300b771aa50a2") # AP TILT
    # MSG = PlatformMessage("020000002c5247eb02f6000098e00003001301a7013b006a006d02910000000000000000036a0688")         # Periodic Diag Message 1
    # MSG = PlatformMessage("020000002c5247eb02f7000098e1683b00000000000000000000033d0002934c000b4ffb000278c2")         # Periodic Diag Message 2
    # MSG = PlatformMessage("020000002c5247eb02f8000098e2000015a500000000000f040008f7000000000036000000000000")         # Periodic Diag Message 3

    ####### Example payloads UL v2 Extended #######
    # MSG = PlatformMessage("010400002d0b155100100000d0601421018da466c90113b837b2df60e0b837b2df60e1b837b2df88c0")       # WiFi AP + cell ID
