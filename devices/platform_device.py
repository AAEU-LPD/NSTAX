""" Generic module for Sensolus Platform suported devices.

Purpose of this module is to represent any device (SF/NBIoT/...) that is
connected to the Sensolus backend.

Default interface is the SensolusWebInterface.
"""


import datetime

from NSTA.devices.device import Device
from NSTA.interface.sensolus_web_interface import SensolusWebInterface


class PlatformDevice(Device):
    """Generic platform connected device base class.

    :param name: Unique name label of device
    :type name: str
    :param device_id: Sensolus Device ID, defaults to ""
    :type device_id: str, optional
    """
    def __init__(self, name, device_id=""):
        super().__init__("PlatformDevice", version = 0.1)
        self.device_id = device_id
        self.name = name
        self.interface = None

    def connect(self):
        """Connect to the device interface."""
        self.logger.info("Establish connection for the device: %s", self.name)
        self.interface = SensolusWebInterface()
        self.interface.connect()

    def disconnect(self):
        """Disconnect from the device interface."""
        self.logger.info("Disconnecting the device: %s", self.name)
        self.interface.disconnect()

    def get_frames(self, start_time_utc=None, end_time_utc=None, max_n_frames=10):
        """Get NB-IoT data frames with given conditions.
        A frame can contain 1 or more device messages.

        :param start_time_utc: Returns frames only from this ISO 8601 UTC timestamp onwards, defaults to a day before current UTC time
        :type start_time_utc: str, optional
        :param end_time_utc: Returns frames upto this ISO 8601 UTC timestamp, defaults to current UTC timestamp captured from the system
        :type end_time_utc: str, optional
        :param max_n_frames: Max. number of messages returned, defaults to 50
        :type max_n_frames: int, optional

        :return: List of data frames
        :rtype: list
        """
        current_utc_time_dt = datetime.datetime.utcnow()
        if end_time_utc:
            end_time_utc_url = end_time_utc + "+00:00"
        else:
            # now utc
            end_time_utc_url = current_utc_time_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        if start_time_utc:
            start_time_utc_url = start_time_utc + "+00:00"
        else:
            # a day before end time utc
            start_time_utc_dt = datetime.datetime.strptime(end_time_utc,  "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(days=1)
            start_time_utc_url = start_time_utc_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        self.logger.info("Get dataframes for device: %s", self.device_id)
        resp = self.interface.get(f"/rest/sigfoxdevices/{self.device_id}/sigfoxMessages", parameters={"start": 0, 'limit': max_n_frames, 'from_date': start_time_utc_url, 'to_date': end_time_utc_url, 'not_filter': False})
        if resp.get("message", "") == "no_data_in_time_filter_key":
            self.logger.error("No data frames within given time window !")
        return resp.get("data", [])

    def get_messages(self, start_time_utc=None, end_time_utc=None, max_n_messages=50):
        """Get raw FW maeesages with given conditions.

        :param start_time_utc: Returns messages only from this ISO 8601 UTC timestamp onwards, defaults to a day before current UTC time
        :type start_time_utc: str, optional
        :param end_time_utc: Returns messages upto this ISO 8601 UTC timestamp, defaults to current UTC timestamp captured from the system
        :type end_time_utc: str, optional
        :param max_n_messages: Max. number of messages returned, defaults to 50
        :type max_n_messages: int, optional

        :return: List of messages
        :rtype: list
        """
        messages_received = []
        current_utc_time_dt = datetime.datetime.utcnow()
        if end_time_utc:
            end_time_utc_url = end_time_utc
        else:
            # now utc
            end_time_utc_url = current_utc_time_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        if start_time_utc:
            start_time_utc_url = start_time_utc
        else:
            # a day before end time utc
            start_time_utc_dt = datetime.datetime.strptime(end_time_utc,  "%Y-%m-%dT%H:%M:%S") - datetime.timedelta(days=1)
            start_time_utc_url = start_time_utc_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        self.logger.info("Get messages for device: %s", self.device_id)
        # resp = self.interface.get(f"/rest/sigfoxdevices/{self.device_id}/sigfoxMessages", parameters={"start": 0, 'limit': max_n_messages, 'from_date': start_time_utc_url, 'to_date': end_time_utc_url, 'not_filter': False})
        # dataframes = resp.get("data", [])
        dataframes = self.get_frames(start_time_utc, end_time_utc, max_n_messages)
        for dataframe in dataframes:
            # Frame level
            for message_ in dataframe.get("data", []):
                # Message level
                message_template = message_.copy()
                # Add network diagnostics to messages
                try:
                    # message_template["network_info"] = dataframe["networks"][0].copy()
                    message_template["network_info"] = dataframe["networks"].copy()
                except (KeyError, IndexError) as e_:
                    message_template["network_info"] = []
                messages_received.append(message_template)
        return messages_received

    def push_downlink_payload(self, payload, description):
        """Set a HEX downlink payload to a device.

        :param payload: DL Payload in hex
        :type payload: str
        :param description: Payload description as free text form
        :type description: str

        :returns: True if successful, False otherwise.
        :rtype: bool
        """
        DL_DATA = {
            "deviceId": f"{self.device_id}",
            "bidirPayload": f"{payload}",
            "description": f"{description}"
        }
        try:
            post_status = self.interface.post("/rest/device_setting_queue", data = DL_DATA)
        except ValueError as e_:
            post_status = False
        return post_status

    def clear_downlink_payloads(self):
        """Clear all pending downlink payloads for the device.

        This method retrieves all downlink payloads queued for the device that have not yet been pushed,
        and removes them from the queue.

        :returns: True if all pending payloads were cleared successfully, False otherwise.
        :rtype: bool
        """
        del_status = True
        try:
            get_message = self.interface.get(f"/rest/device_setting_queue/{self.device_id}")
        except ValueError as e_:
            del_status = False
            return del_status
        pending_settings = [item["id"] for item in get_message if "pushedAt" in item and not item["pushedAt"]]
        for pending_setting_id in pending_settings:
            try:
                del_status = self.interface.delete(f"/rest/device_setting_queue/{pending_setting_id}")
            except ValueError as e_:
                del_status = False
        return del_status

    def queue_firmware(self, fw_package):
        """Queue a known FW to the device.

        :param fw_package: FW package name that is already uploaded in the platform
        :type fw_package: str
        """
        FOTA_DATA = {
            "operationType":"QUEUE_FIRMWARE_UPGRADE",
            "devices":[f"{self.device_id}"],
            "queueFirmwareUpgrade":{
                "queueFirmwareUpgradeOption":"NBIOT",
                "queueFirmwareUpgradeVersion":"ALL",
                "firmwareShaKey":f"{fw_package}",
                "clearPendingFirmwareUpgrade":False}
            }
        post_status = self.interface.post("/rest/bulk_device_operations/TRACKER", data = FOTA_DATA)
        return post_status

    def clear_queue_firmware_upgrade(self):
        """clear a queue for a firmware upgrade.
        """
        FOTA_DATA = {
            "operationType":"CLEAR_QUEUE_FIRMWARE_UPGRADE",
            "devices":[f"{self.device_id}"],
            }
        post_status = self.interface.post("/rest/bulk_device_operations/TRACKER", data = FOTA_DATA)
        return post_status


if __name__ == "__main__":
    # Example run
    NDD = PlatformDevice("4CULK2", device_id=780734)
    NDD.connect()
    messages = NDD.get_messages(start_time_utc="2025-09-24T15:15:00", end_time_utc="2025-09-24T15:30:00", max_n_messages=100)
    # messages = NDD.get_frames(start_time_utc="2025-09-16T00:00:00", end_time_utc="2025-09-16T11:20:00", max_n_frames=100)
    print(messages)
    # NDD.push_downlink_payload("b007e00000000006", "Set DL Interval to 5 Hours")
    # NDD.clear_downlink_payloads()
    NDD.disconnect()
    # ExampleDiagFrameWithMultipleNetworkParam = {
    #     'backendSeqNbr': 947,
    #     'data':[
    #         {
    #             'decodedMsg': {
    #                 'header': {
    #                 'containsDiMessageId': False,
    #                 'diAck': False,
    #                 'logicSequenceNumber': 899,
    #                 'messageGenerationTime': '2024-06-27T17:21:40+0000'
    #                 },
    #                 'messageDate': '2024-06-27T17:21:40+0000',
    #                 'messageId': 0,
    #                 'messageTimeAvailable': True,
    #                 'messageType': 'ALPS_STATUS',
    #                 'payload': {
    #                 'alpsMessageType': 'STATUS_DOWNLINK_REQUEST',
    #                 'continueRequestFlag': False,
    #                 'errorCodeForPrevious': 'OK',
    #                 'header': {
    #                     'ackSeqNr': 0,
    #                     'batteryStatus': 'EXCELLENT'
    #                 },
    #                 'isFirstRequestAfterStartUp': False,
    #                 'isPendingRequest': False,
    #                 'isRepeatedRequest': False,
    #                 'majorVer': 35,
    #                 'minorVer': 0,
    #                 'patchVer': 0,
    #                 'sequenceNbr': 0
    #                 }
    #             },
    #             'downlinkMsg': {
    #                 'fwparams': [],
    #                 'payload': 'B20000000000000F',
    #                 'type': 'REMOTE_SETTING'
    #             },
    #             'rawMsg': {
    #                 'backendSeqNbr': 947,
    #                 'bidirPayload': 'B20000000000000F',
    #                 'bidirectional': True,
    #                 'dataDecoded': '010000002e105c24038300000000000000000000e8000c2300009c',
    #                 'dataEncoded': '010000002e105c24038300000000000000000000e8000c2300009c',
    #                 'deviceMessageOriginSource': 'CELLULAR',
    #                 'duplicates': [],
    #                 'firstReceiveTime': '2024-06-27T17:22:08+0000',
    #                 'id': 3143137157,
    #                 'messageId': 0,
    #                 'payloadType': 'REMOTE_SETTING',
    #                 'previousReceiveTimes': [],
    #                 'source': 'INTERNAL'
    #             }
    #         }
    #     ],
    #     'deviceMessageOriginSource': 'CELLULAR',
    #     'firstReceiveTime': '2024-06-27T17:22:08+0000',
    #     'networks': [
    #         {
    #             'decodedMsg': {
    #                 'data': {
    #                     'ecl': '0',
    #                     'lac': 'A76C',
    #                     'operator': '26202',
    #                     'psm_config_active': '0',
    #                     'psm_config_tau': '1152000',
    #                     'psm_enabled': 'false',
    #                     'rsrp': '-84',
    #                     'rsrpLabel': 'good',
    #                     'rsrq': '-5',
    #                     'rsrqLabel': 'excellent',
    #                     'sc_band': '20',
    #                     'sc_cellid': '5195110',
    #                     'sc_tx_pwr': '90'
    #                 },
    #                 'messageId': 0,
    #                 'messageTimeAvailable': False,
    #                 'messageType': 'NBIOT_DIAGNOSTICS',
    #                 'operatorInfo': {
    #                 'brand': 'Vodafone',
    #                 'countryCode': 'DE',
    #                 'countryName': 'Germany',
    #                 'mcc': '262',
    #                 'mnc': '02',
    #                 'operator': 'Vodafone D2 GmbH'
    #                 }
    #             },
    #             'rawMsg': {
    #                 'backendSeqNbr': 947,
    #                 'bidirectional': False,
    #                 'dataDecoded': '{"data":{"sc_band":"20","psm_enabled":"false","sc_tx_pwr":"90","rsrqLabel":"excellent","rsrp":"-84","operator":"26202","ecl":"0","lac":"A76C","rsrq":"-5","rsrpLabel":"good","psm_config_active":"0","psm_config_tau":"1152000","sc_cellid":"5195110"},"operatorInfo":{"countryName":"Germany","countryCode":"DE","mcc":"262","mnc":"02","brand":"Vodafone","operator":"Vodafone '
    #                             'D2 '
    #                             'GmbH"},"messageType":"NBIOT_DIAGNOSTICS","replay":false,"messageId":0,"messageTimeAvailable":false}',
    #                 'dataEncoded': '{"data":{"sc_band":"20","psm_enabled":"false","sc_tx_pwr":"90","rsrqLabel":"excellent","rsrp":"-84","operator":"26202","ecl":"0","lac":"A76C","rsrq":"-5","rsrpLabel":"good","psm_config_active":"0","psm_config_tau":"1152000","sc_cellid":"5195110"},"operatorInfo":{"countryName":"Germany","countryCode":"DE","mcc":"262","mnc":"02","brand":"Vodafone","operator":"Vodafone '
    #                             'D2 '
    #                             'GmbH"},"messageType":"NBIOT_DIAGNOSTICS","replay":false,"messageId":0,"messageTimeAvailable":false}',
    #                 'deviceMessageOriginSource': 'CELLULAR',
    #                 'duplicates': [],
    #                 'estimatedLat': 53.059295,
    #                 'estimatedLng': 9.650959,
    #                 'firstReceiveTime': '2024-06-27T17:22:08+0000',
    #                 'id': 3143137161,
    #                 'messageId': 0,
    #                 'previousReceiveTimes': [],
    #                 'radius': 15082,
    #                 'source': 'INTERNAL'
    #             }
    #         },
    #         {
    #             'decodedMsg': {
    #                 'data': {
    #                     'deepsleep_timeout_count': '0',
    #                     'ecl0_count': '810',
    #                     'ecl1_count': '37',
    #                     'ecl2_count': '6',
    #                     'modem_active_time_s': '2142',
    #                     'modem_cereg_search_time_s': '102',
    #                     'modem_connect_count': '8',
    #                     'modem_deepsleep_wake_time_s': '14227',
    #                     'modem_disconnect_count': '0',
    #                     'modem_no_rx_timeout_count': '2',
    #                     'modem_poweroff_count': '0',
    #                     'modem_psm_wake_time_s': '6713',
    #                     'modem_restart_count': '2',
    #                     'modem_rx_failed_count': '5',
    #                     'network_reject_count': '1',
    #                     'pdp_repair_count': '0'
    #                 },
    #                 'messageId': 0,
    #                 'messageTimeAvailable': False,
    #                 'messageType': 'NBIOT_DIAGNOSTICS'
    #             },
    #             'rawMsg': {
    #                 'backendSeqNbr': 947,
    #                 'bidirectional': False,
    #                 'dataDecoded': '{"data":{"modem_poweroff_count":"0","modem_active_time_s":"2142","deepsleep_timeout_count":"0","modem_restart_count":"2","modem_disconnect_count":"0","network_reject_count":"1","modem_deepsleep_wake_time_s":"14227","ecl0_count":"810","modem_no_rx_timeout_count":"2","modem_rx_failed_count":"5","modem_cereg_search_time_s":"102","modem_psm_wake_time_s":"6713","ecl1_count":"37","pdp_repair_count":"0","modem_connect_count":"8","ecl2_count":"6"},"messageType":"NBIOT_DIAGNOSTICS","replay":false,"messageId":0,"messageTimeAvailable":false}',
    #                 'dataEncoded': '{"data":{"modem_poweroff_count":"0","modem_active_time_s":"2142","deepsleep_timeout_count":"0","modem_restart_count":"2","modem_disconnect_count":"0","network_reject_count":"1","modem_deepsleep_wake_time_s":"14227","ecl0_count":"810","modem_no_rx_timeout_count":"2","modem_rx_failed_count":"5","modem_cereg_search_time_s":"102","modem_psm_wake_time_s":"6713","ecl1_count":"37","pdp_repair_count":"0","modem_connect_count":"8","ecl2_count":"6"},"messageType":"NBIOT_DIAGNOSTICS","replay":false,"messageId":0,"messageTimeAvailable":false}',
    #                 'deviceMessageOriginSource': 'CELLULAR',
    #                 'duplicates': [],
    #                 'firstReceiveTime': '2024-06-27T17:22:08+0000',
    #                 'id': 3143137160,
    #                 'messageId': 0,
    #                 'previousReceiveTimes': [],
    #                 'source': 'INTERNAL'
    #             }
    #         }
    #     ]
    # }
