"""Test Suite for HATI Cell ID Geolocation Feature."""

from NSTA.testscripts.test_script import TestScript

from time import sleep
from datetime import datetime, timezone, timedelta


class HATI_Connectivity_Utils():
    def __init__(self):
        self.magnet_duration_s = 10
        self.shake_duration_s = 120
        self.config_sync_time_min = 2
        
    # ---  Device Configs --- #
    def _set_back_to_activation(self, device):
        activation_payload = "0000fa000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000035"
        device.clear_downlink_payloads()
        device.push_downlink_payload(activation_payload, "automation_back_to_activation")

    def _set_profile_preset(self, device, preset=None):
        if preset == "default":
            profile_preset_payload = "0000ff280000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000050"
        elif preset == "5min_stop_timeout":
            # Shorter periodic DL
            # Shorter stop DL
            profile_preset_payload = "xxxx"
            return
        elif preset == "10min_keepalive_test":
            profile_preset_payload = "000019fffff8000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000042"
        else:
            return
        device.clear_downlink_payloads()
        device.push_downlink_payload(profile_preset_payload, "automation_set_profile_preset")

    # ---  Equipment Control --- #
    def _execute_magnet_sequence(self, magnet, label, magnet_duration=None):
        if magnet_duration is None:
            magnet_duration = self.magnet_duration_s
        magnet.start_magnet(label)
        sleep(magnet_duration)
        magnet.stop_magnet(label)

    def _execute_shaker_sequence(self, shaker, label, shake_duration=None):
        if shake_duration is None:
            shake_duration = self.shake_duration_s
        shaker.start_shaking(label)
        sleep(shake_duration)
        shaker.stop_shaking(label)

    def _execute_ecl_sequence(self, callbox, ecl, NETWORK_MODE, BAND):
        callbox.change_network_bands(NETWORK_MODE, BAND, BAND, BAND, coverage_levels=True)
        sleep(10)
        if ecl == 0:
            callbox.trigger_ecl_0_all_cells()
        elif ecl == 1:
            callbox.trigger_ecl_1_all_cells()
        elif ecl == 2:
            callbox.trigger_ecl_2_all_cells()
        else:
            raise ValueError("Invalid ECL value. Use 0, 1, or 2.")

    def _execute_network_outage_sequence(self, callbox, NETWORK_MODE, BAND, outage_mode, outage_time):
        callbox.change_network_bands(NETWORK_MODE, BAND, BAND, BAND, coverage_levels=False)
        sleep(10)
        if outage_mode == "NO_INTERNET":
            callbox.trigger_no_internet(outage_time)
        elif outage_mode == "NO_NETWORK":
            callbox.trigger_no_network(outage_time)
        elif outage_mode == "FULL_SERVICE":
            callbox.reset_cells_gain()
        else:
            raise ValueError("Invalid outage mode. Use 'NO_INTERNET' or 'NO_NETWORK'.")

    # ---  Message Parsing ---#
    def _check_activation_messages(self, messages):
        """Checks if a activation messages are present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if activation msg is present)/False (if not present) + activation Message/None
        :rtype: bool, dict
        """
        boot_true, boot_msg = self._check_boot_message(messages)
        keepalive_true, keepalive_msg = self._check_keepalive_message(messages)
        if keepalive_true:
            if boot_true: 
                return True, boot_msg, keepalive_msg
            return True, None, keepalive_msg
        return False, None, None
    
    def _check_location_messages(self, messages):
        """Checks if a location messages are present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if location msg is present)/False (if not present) + location Message/None
        :rtype: bool, dict
        """
        start_true, start_msg = self._check_start_message(messages)
        stop_true, stop_msg = self._check_stop_message(messages)
        keepalive_true, keepalive_msg = self._check_keepalive_message(messages)
        if start_true and stop_true:
            if keepalive_true:
                return True, start_msg, stop_msg, keepalive_msg
            return True, start_msg, stop_msg, None
        return False, None, None, None

    def _check_periodic_message(self, messages):
        """Checks if a periodic messages are present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if periodic msg is present)/False (if not present) + periodic Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            message_type = msg["decodedMsg"]["messageType"]
            if message_type == "KEEP_ALIVE_EVENT":
                event_type = msg["decodedMsg"]["event"]
                if event_type == "PERIODIC":
                    return True, msg
        return False, None

    def _check_boot_message(self, messages):
        """Checks if a boot message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if boot msg is present)/False (if not present) + boot Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            message_type = msg["decodedMsg"]["messageType"]
            if message_type == "BOOT_EVENT":
                return True, msg
        return False, None

    def _check_keepalive_message(self, messages):
        """Checks if a keepalive message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if keepalive msg is present)/False (if not present) + keepalive Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            message_type = msg["decodedMsg"]["messageType"]
            if message_type == "KEEP_ALIVE_EVENT":
                return True, msg
        return False, None

    def _check_start_message(self, messages):
        """Checks if a stop message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if keepalive msg is present)/False (if not present) + keepalive Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            message_type = msg["decodedMsg"]["messageType"]
            if message_type == "LOCATION_UPDATE":
                location_state = msg["decodedMsg"]["state"]
                if location_state == "START":
                    return True, msg
        return False, None

    def _check_stop_message(self, messages):
        """Checks if a stop message is present in a list of messages

        :param messages: list of messages
        :type messages: list
        :return: True (if keepalive msg is present)/False (if not present) + keepalive Message/None
        :rtype: bool, dict
        """
        for msg in messages:
            message_type = msg["decodedMsg"]["messageType"]
            if message_type == "LOCATION_UPDATE":
                location_state = msg["decodedMsg"]["state"]
                if location_state == "STOP":
                    return True, msg
        return False, None

    def _check_ecl_level(self, message, set_ecl_level):
        """Checks if the ecl level assigned to the network message is correct

        :param message: network message with ECL info
        :type message: dict
        :param set_ecl_level: assigned network ECL level
        :type set_ecl_level: str
        :return: True(If network corresponds to set network ECL level)/False(If network is mismatched)
        :rtype: bool, str
        """
        data = message["network_info"][0]
        if data is not None:
            ecl_level = int(data["decodedMsg"]["data"]["ecl"])
            if ecl_level == set_ecl_level:
                return True, ecl_level
            return False, ecl_level
        return False, None

    def _check_network_outage_uptime(self, message, uptime_limit_h=0):
        """Checks if the uptime of the network message is correct

        :param message: network message with uptime info
        :type message: dict
        :return: True(If network corresponds to set network uptime)/False(If network is mismatched)
        :rtype: bool, str
        """
        data = message["decodedMsg"]["keepAliveMetricValues"]
        if data is not None:
            uptime = data["UPTIME_IN_HOUR"]
            wake_time = data["CPU_WAKETIME"]
            if uptime >= uptime_limit_h:
                return True, uptime, wake_time
        return False, uptime, wake_time

    def _check_periodic_timestamps(self, periodic_message, timestamp_wait_buffer=0):
        """
        Checks if the timestamps of the periodic message are valid.
        
        Validates that:
            - The timestamp is in the past compared to the current UTC time.
            - The timestamp is at least `timestamp_wait_buffer` minutes in the past.

        :param periodic_message: The message containing the periodic timestamp.
        :type periodic_message: dict
        :param timestamp_wait_buffer: Minimum number of minutes the timestamps should be in the past.
        :type timestamp_wait_buffer: int
        :return: Tuple of (True, timestamps) if valid, otherwise (False, timestamps).
        :rtype: tuple(bool, dict)
        """
        periodic_timestamp = periodic_message["decodedMsg"]["messageDate"]
        # Parse the timestamps to datetime objects
        periodic_dt = datetime.strptime(periodic_timestamp, "%Y-%m-%dT%H:%M:%S%z")

        # Get current UTC time in the same format
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

        # Example comparison: check if stop_dt is before now
        timestamps = {
            "periodic": periodic_dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "now": now_str
        }
        # Check if message is in the past compared to now
        min_delta = timestamp_wait_buffer * 60  #
        if (
            periodic_dt <= now_dt and
            (now_dt - periodic_dt).total_seconds() >= min_delta
        ):
            return True, timestamps
        return False, timestamps
    
    def _check_location_timestamps(self, start_message, stop_message, timestamp_wait_buffer):
        """
        Checks if the timestamps of the start and stop location messages are valid.

        Validates that:
            - Both timestamps are in the past compared to the current UTC time.
            - The start timestamp is less than or equal to the stop timestamp.
            - Both timestamps are at least `timestamp_wait_buffer` minutes in the past.

        :param start_message: The message containing the start timestamp.
        :type start_message: dict
        :param stop_message: The message containing the stop timestamp.
        :type stop_message: dict
        :param timestamp_wait_buffer: Minimum number of minutes the timestamps should be in the past.
        :type timestamp_wait_buffer: int
        :return: Tuple of (True, timestamps) if valid, otherwise (False, timestamps).
        :rtype: tuple(bool, dict)
        """
        start_timestamp = start_message["decodedMsg"]["messageDate"]
        stop_timestamp = stop_message["decodedMsg"]["messageDate"]
        # Parse the timestamps to datetime objects
        start_dt = datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%S%z")
        stop_dt = datetime.strptime(stop_timestamp, "%Y-%m-%dT%H:%M:%S%z")

        # Get current UTC time in the same format
        now_dt = datetime.now(timezone.utc)
        now_str = now_dt.strftime("%Y-%m-%dT%H:%M:%S%z")

        # Example comparison: check if stop_dt is before now
        timestamps = {
            "start": start_dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "stop": stop_dt.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "now": now_str
        }
        # Both start and stop must be at least 10 minutes in the past compared to now
        min_delta = timestamp_wait_buffer * 60  # 10 minutes in seconds
        if (
            start_dt <= stop_dt <= now_dt and
            (now_dt - start_dt).total_seconds() >= min_delta and
            (now_dt - stop_dt).total_seconds() >= min_delta
        ):
            return True, timestamps
        return False, timestamps
    
    # --- Misc Formatting --- #
    def create_network_info_html(self, fullMsg):
        if fullMsg is None:
            return "<div>No NETWORK_INFO message received</div>"
        data = fullMsg["decodedMsg"]["data"]
        operatorInfo = fullMsg["decodedMsg"]["operatorInfo"]
        # Helpers for label styling
        def label_span(label, value):
            colors = {
                "excellent": "background-color:#39cb99; color:white; padding:2px 6px; border-radius:4px;",
                "poor": "background-color:#e00000; color:white; padding:2px 6px; border-radius:4px;",
                "good": "background-color:#ffa858; color:white; padding:2px 6px; border-radius:4px;",
                "0": "background-color:#39cb99; color:white; padding:2px 6px; border-radius:4px;",
                "1": "background-color:#ffa858; color:white; padding:2px 6px; border-radius:4px;",
                "2": "background-color:#e00000; color:white; padding:2px 6px; border-radius:4px;",
                "255": "background-color:#e00000; color:white; padding:2px 6px; border-radius:4px;"
            }
            return f'<span style="{colors.get(label, "")}"> {label} {value}</span>'
        # PSM time formatting (tau is in seconds)
        tau_seconds = int(data.get("psm_config_tau", 0))
        tau_fmt = str(timedelta(seconds=tau_seconds))
        html = f"""
        <div style="font-family:Roboto, sans-serif;font-size:small ;line-height:1.5;background:#FFFFFF;margin:10px;padding:10px 30px;border-radius:10px;border:1px solid #0a4058;">
            <h3>NETWORK_INFO</h3>
            <div>
                <b>ecl:  </b> {label_span(data.get("ecl", ""), "")},
                <b>rsrp: </b> {label_span(data.get("rsrpLabel", ""), data.get("rsrp")+'dBm')},
                <b>rsrq: </b> {label_span(data.get("rsrqLabel", ""), data.get("rsrq")+'dBm')},
            </div>
            <div>
                <b>tx_power:</b> {data.get("sc_tx_pwr")}dBm
            </div>
            <div>
                <b>psm:</b> tau: {tau_fmt} , active: {data.get("psm_config_active")}
            </div>
            <div>
                <b>operator:</b>
                <ul style="margin:0;">
                    <li><i>{operatorInfo.get("operator")} brand:</i> {operatorInfo.get("brand")}</li>
                </ul>
            </div>
            <div>
                <b>cell data:</b>
                <ul style="margin:0;">
                    <li>
                        <i>band:</i> {data.get("sc_band")}
                        <i>lac:</i> {data.get("lac")}
                        <i>cell:</i> {data.get("sc_cellid")}
                        <i>operator:</i> {data.get("operator")}
                    </li>
                </ul>
            </div>
            <div>
                <b>other:</b>
                <ul style="margin:0;">
                    <li><i>lte_mode:</i> {data.get("lte_mode")}</li>
                    <li><i>sim_type:</i> {data.get("sim_type")}</li>
                </ul>
            </div>
            <div>
                <b>ecl0:</b> <span style="background:#39cb99;color:white;padding:2px 6px;border-radius:4px;">346</span>,
                <b>ecl1:</b> <span style="background:#ffa858;color:white;padding:2px 6px;border-radius:4px;">2</span>,
                <b>ecl2:</b> <span style="background:#e00000;color:white;padding:2px 6px;border-radius:4px;">10</span>
            </div>
            <br>
        </div>
        """
        return html

    def create_boot_event_html(self, fullMsg):
        if fullMsg is None:
            return "<div>No BOOT_EVENT message received</div>"
        data = fullMsg['decodedMsg']
        raw = fullMsg['rawMsg']
        html = f"""
        <div style="font-family:Roboto, sans-serif;font-size:small ;line-height:1.5;background:#FFFFFF;margin:10px;padding:10px 30px;border-radius:10px;border:1px solid #0a4058;">
            <h4><i>{datetime.strptime(raw.get("firstReceiveTime"), "%Y-%m-%dT%H:%M:%S%z").strftime("%d-%m-%Y, %H:%M:%S")}</i></h4>
            <h3>BOOT_EVENT</h3>
            <div><b>messageDate:</b> {data.get("messageDate")}</div>
            <div><b>hardwareID:</b> {data.get("hardwareID")}</div>
            <div><b>firmware:</b> v{data.get("fwVersionMajor")}.{data.get("fwVersionMinor")} ({data.get("firmwareSHA")})</div>
            <div><b>bootloaderVersion:</b> {data.get("bootloaderVersion")}</div>
            <div><b>modemRevision:</b> {data.get("modemRevision")}</div>
            <div><b>wifiRevision:</b> {data.get("wifiRevision")}</div>
            <div><b>batteryVoltage:</b> {int(data.get("batteryVoltage", 0)) / 1000:.2f} V</div>
            <div><b>bootReason:</b> {data.get("bootReason")}</div>
            <div><b>sleepTime:</b> {data.get("sleepTime")} s</div>
            <div><b>identifiers:</b>
                <ul style="margin:0;">
                    <li><i>imei:</i> {data.get("imei")}</li>
                    <li><i>iccid:</i> {data.get("iccid")}</li>
                </ul>
            </div>
            <br>
        </div>
        """
        return html

    def create_keep_alive_event_html(self, fullMsg):
        if fullMsg is None:
            return "<div>No KEEP_ALIVE_EVENT message received</div>"
        data = fullMsg['decodedMsg']
        raw = fullMsg['rawMsg']
        metrics = data.get("keepAliveMetricValues", {})
        # Helper to format battery voltage in volts if it looks like mV
        def format_voltage(val):
            try:
                v = float(val)
                if v > 100:  # millivolts
                    return f"{v/1000:.2f} V"
                return f"{v} V"
            except:
                return val
        html = f"""
        <div style="font-family:Roboto, sans-serif;font-size:small ;line-height:1.5;background:#FFFFFF;margin:10px;padding:10px 30px;border-radius:10px;border:1px solid #0a4058;">
            <h4><i>{datetime.strptime(raw.get("firstReceiveTime"), "%Y-%m-%dT%H:%M:%S%z").strftime("%d-%m-%Y, %H:%M:%S")}</i></h4>
            <h3 style="color:blue">KEEP_ALIVE_EVENT</h3>
            <div><b>messageDate:</b> {data.get("messageDate")}</div>
            <div><b>Firmware SHA:</b> {metrics.get("FIRMWARE_SHA")}</div>
            <div><b>Modem SHA:</b> {metrics.get("MODEM_FIRMWARE_SHA")}</div>
            <div><b>uptime:</b> {metrics.get("UPTIME_IN_HOUR")} h</div>
            <div><b>CPU wake time:</b> {metrics.get("CPU_WAKETIME")} min</div>
            <div><b>metrics:</b>
                <ul style="margin:0;">
                    <li><i>energy consumed:</i> {metrics.get("ENERGY_CONSUMED")} uAh</li>
                    <li><i>energy depassivation:</i> {metrics.get("ENERGY_DEPASSIVATION")} uAh</li>
                    <li><i>modem connect count:</i> {metrics.get("MODEM_CONNECT_COUNT")}</li>
                    <li><i>modem restart count:</i> {metrics.get("MODEM_RESTART_COUNT")}</li>
                    <li><i>modem poweroff count:</i> {metrics.get("MODEM_POWEROFF_COUNT")}</li>
                    <li><i>modem active time:</i> {metrics.get("MODEM_ACTIVE_TIME_S")} s</li>
                    <li><i>modem PSM wake time:</i> {metrics.get("MODEM_PSM_WAKE_TIME_S")} s</li>
                    <li><i>modem deep sleep wake time:</i> {metrics.get("MODEM_DEEPSLEEP_WAKE_TIME_S")} s</li>
                    <li><i>modem CREG search time:</i> {metrics.get("MODEM_CREG_SEARCH_TIME_S")} s</li>
                    <li><i>GPS cumulative fix time:</i> {metrics.get("GPS_CUMULATIVE_FIX_TIME")} s</li>
                    <li><i>GPS total requests:</i> {metrics.get("GPS_TOTAL_NUMBER_REQUEST")}</li>
                    <li><i>temperature:</i> {metrics.get("TEMPERATURE")} °C</li>
                    <li><i>min temp (24h):</i> {metrics.get("MIN_TEMPERATURE_24H")} °C</li>
                    <li><i>max temp (24h):</i> {metrics.get("MAX_TEMPERATURE_24H")} °C</li>
                    <li><i>VBAT min temp:</i> {format_voltage(metrics.get("VBAT_MIN_TEMP"))}</li>
                    <li><i>VBAT max temp:</i> {format_voltage(metrics.get("VBAT_MAX_TEMP"))}</li>
                    <li><i>external power voltage:</i> {format_voltage(metrics.get("EXTERNAL_POWER_VOLTAGE"))}</li>
                </ul>
            </div>
            <br>
        </div>
        """
        return html
    
    def create_location_event_html(self, fullMsg):
        if fullMsg is None:
            return "<div>No LOCATION_UPDATE message received</div>"
        data = fullMsg['decodedMsg']
        raw = fullMsg['rawMsg']
        html = f"""
        <div style="font-family:Roboto, sans-serif;font-size:small ;line-height:1.5;background:#FFFFFF;margin:10px;padding:10px 30px;border-radius:10px;border:1px solid #0a4058;">
            <h4><i>{datetime.strptime(raw.get("firstReceiveTime"), "%Y-%m-%dT%H:%M:%S%z").strftime("%d-%m-%Y, %H:%M:%S")}</i></h4>
            <h3 style="color:green">LOCATION_UPDATE</h3>
            <div><b>messageDate:</b> {data.get("messageDate")}</div>
            <div><b>state:</b> {data.get("state")}</div>
            <div><b>source:</b> {data.get("source")}</div>
            <div><b>latitude:</b> {data.get("latitude")}</div>
            <div><b>longitude:</b> {data.get("longitude")}</div>
            <div><b>accuracy:</b>
                <ul style="margin:0;">
                    <li><i>fixTime:</i> {data.get("fixTime")}</li>
                    <li><i>fixState:</i> {data.get("fixState")}</li>
                </ul>
            </div>
            <div><b>cell Params:</b>
                <ul style="margin:0;">
                    <li><i>mcc:</i> {data.get("mcc")}</li>
                    <li><i>mnc:</i> {data.get("mnc")}</li>
                    <li><i>cellId:</i> {data.get("cellId")}</li>
                    <li><i>lac:</i> {data.get("lac")}</li>
                </ul>
            </div>
            <br>
        </div>
        """
        return html
    
    def create_ka_stop_event_html(self, fullMsg):
        if fullMsg is None:
            return "<div>No KEEP_ALIVE_EVENT message received</div>"
        data = fullMsg["decodedMsg"]
        raw = fullMsg["rawMsg"]
        html = f"""
        <div style="font-family:Roboto, sans-serif;font-size:small ;line-height:1.5;background:#FFFFFF;margin:10px;padding:10px 30px;border-radius:10px;border:1px solid #0a4058;">
            <h4><i>{datetime.strptime(raw.get("firstReceiveTime"), "%Y-%m-%dT%H:%M:%S%z").strftime("%d-%m-%Y, %H:%M:%S")}</i></h4>
            <h3 style="color:blue">KEEP_ALIVE_EVENT</h3>
            <div><b>messageDate:</b> {data.get("messageDate")}</div>
            <div><b>event:</b> {data.get("event")}</div>
        </div>
        """
        return html


class HATI_Connectivity_Activation_Base(TestScript):
    """Testing the Activation sequence in an ECL = 0, 1 or 2 or no network/internet scenarios

    This testcase uses the Profile Info config to set the device Back to Activation and
    test a specific network scenario.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is attached to the NSTA Magnet station
        - Device is unactivated
        - Device is in an ECL condition (0, 1 or 2) with Coverage Level enabled
        or
        - Device is in a Network Outage condition (No Network or No Internet)
    """

    def __init__(self):
        super().__init__()
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.requirement["EQUIPMENT"].append("NSTA25MV")
        self.n_steps = 4
        self.version = 0.1
        self.ecl_level = None
        self.outage_mode = None
        self.outage_time_hr =  None
        self.test_type = None
        if type(self) is HATI_Connectivity_Activation_Base:
            raise TypeError("HATI_Connectivity_Activation_Base cannot be instantiated directly")

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        PRE_CONFIG = test_parameters.get("pre_config", False)
        WAIT_TIME = test_parameters.get("downlink_wait_time_min", 5)
        CIOT_TIMEOUT = test_parameters.get("ciot_timeout_min", 0)
        NETWORK_TIMEOUT = test_parameters.get("network_outage_min", 0)
        NETWORK_MODE = test_parameters.get("network_mode", "both")
        STATION_LABEL = test_parameters.get("station_label", "B")
        BAND = test_parameters.get("band", 20)
        utils = HATI_Connectivity_Utils()

        # --- Step X: Setup Equipment --- #
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
            if equ.name == "NSTA25MV":
                magnet = equ
        callbox.reset_cells_gain()

        # --- Step Y: Setup Device --- #
        device = self.DUT
        if PRE_CONFIG:
            sync_time = utils.config_sync_time_min * 60
            utils._set_back_to_activation(device)
            utils._execute_magnet_sequence(magnet, STATION_LABEL)
            sleep(sync_time)
            self.logger.info("Test-Execution|Preconfig: Setting back to Activation")

        # --- Step 1: Modify network configs --- #
        if self.test_type == "ecl":
            self.step_start(step_no=1, step_description=f"Modify Network Mode and Band", expected_result=f"-")
            utils._execute_ecl_sequence(callbox, ecl=self.ecl_level, NETWORK_MODE=NETWORK_MODE, BAND=BAND)
            self.logger.info("Test-Execution|Preconfig: Setting ENB Config")
            self.step_end(actual_result=f"Network modified to <ul><li>{NETWORK_MODE} network mode</li> <li>Band {BAND}</li> <li>ECL {self.ecl_level}</li> <li>Coverage Level Enabled</li></ul>", step_verdict="PASSED")
        elif self.test_type == "network":
            self.step_start(step_no=1, step_description=f"Modify Network Outage and Band", expected_result=f"-")
            utils._execute_network_outage_sequence(callbox, NETWORK_MODE=NETWORK_MODE, BAND=BAND, outage_mode=self.outage_mode, outage_time=NETWORK_TIMEOUT)
            self.logger.info(f"Test-Execution|Preconfig: Setting Network to outage mode: {self.outage_mode}")
            self.step_end(actual_result=f"Network modified to <ul><li>{NETWORK_MODE} network mode</li> <li>Band {BAND}</li> <li>Outage Mode {self.outage_mode}</li> <li>for {NETWORK_TIMEOUT} minutes</li></ul>", step_verdict="PASSED")
        else:
            raise ValueError("Invalid test_type. Use 'ecl' or 'network'.")

        # --- Step 2: Activate Device --- #
        self.step_start(step_no=2, step_description=f"Using Magnet Station {STATION_LABEL} to Activate the Device", expected_result=f"-")
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        utils._execute_magnet_sequence(magnet, STATION_LABEL)
        self.logger.info("Test-Execution|Activation: Triggering Magnet")
        self.step_end(actual_result=f"Magnet started and stopped successfully", step_verdict="PASSED")

        # --- Step 3: Check Activation Message --- #
        self.step_start(step_no=3, step_description=f"Check Activation message on Station:{STATION_LABEL} after {WAIT_TIME+CIOT_TIMEOUT} minutes", expected_result=f"Activation messages received successfully in the backend")
        sleep((WAIT_TIME+2)*60)
        sleep(CIOT_TIMEOUT*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        messages_received, boot_msg, activation_msg = utils._check_activation_messages(backend_messages_t)
        if messages_received:
            self.logger.info("Activation messages received successfully")
            self.step_end(actual_result=f"Received activation messages successfully. {utils.create_boot_event_html(boot_msg)}{utils.create_keep_alive_event_html(activation_msg)}", step_verdict="PASSED")
            
            if self.test_type == "ecl":
                # --- Step 4: Check valid ECL level --- #
                self.step_start(step_no=4, step_description="Evaluate ECL level validity", expected_result=f"ECL level is valid according to set level: {self.ecl_level}")
                ecl_valid, ecl_level = utils._check_ecl_level(activation_msg, set_ecl_level=self.ecl_level)
                if ecl_valid:
                    self.logger.info(f"Reported ECL is valid: {ecl_level}")
                    self.step_end(actual_result=f"Reported ECL ({ecl_level}) is valid. {utils.create_network_info_html(activation_msg['network_info'][0])}", step_verdict="PASSED")
                else:
                    self.logger.info(f"Reported ECL is invalid: {ecl_level}")
                    self.step_end(actual_result=f"Reported ECL is invalid: {ecl_level}", step_verdict="FAILED")
            elif self.test_type == "network":
                # --- Step 4: Check Network Outage uptime --- #
                self.step_start(step_no=4, step_description="Check Network Outage uptime", expected_result="Network Outage uptime is valid")
                uptime_valid, uptime, waketime = utils._check_network_outage_uptime(activation_msg, uptime_limit_h=0)
                if uptime_valid:
                    self.logger.info(f"Network Outage uptime is valid: {uptime}h, Wake time: {waketime} mins")
                    self.step_end(actual_result=f"Network Outage uptime is valid: {uptime}h, Wake time: {waketime} mins", step_verdict="PASSED")
                else:
                    self.logger.info(f"Network Outage uptime is invalid: {uptime}h, Wake time: {waketime} mins")
                    self.step_end(actual_result=f"Network Outage uptime is invalid: {uptime}h, Wake time: {waketime} mins", step_verdict="FAILED")
            else:
                raise ValueError("Invalid test_type. Use 'ecl' or 'network'.")
        else:
            self.logger.info("Test Failed: No Activation messages received or missing message. Check the backend")
            self.step_end(actual_result=f"Did not receive a activation messages or missing message. Check the backend", step_verdict="FAILED")

        # --- Step Z: Return to default settings --- #
        callbox.reset_cells_gain()
        
        
class HATI_Connectivity_Location_Base(TestScript):
    """Testing the Location sequence in an Full service, no netork/internet scenarios

    This testcase uses a standard profile to test a specific network scenario with location triggers.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is attached to the NSTA Vibration station
        - Device is activated
        - Device is in Full service or a Network Outage condition (No Network or No Internet)
    """

    def __init__(self):
        super().__init__()
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.requirement["EQUIPMENT"].append("NSTA25MV")
        self.n_steps = 4
        self.version = 0.1
        self.outage_mode = None
        if type(self) is HATI_Connectivity_Location_Base:
            raise TypeError("HATI_Connectivity_Location_Base cannot be instantiated directly")

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        PRE_CONFIG = test_parameters.get("pre_config", False)
        WAIT_TIME = test_parameters.get("downlink_wait_time_min", 5)
        CIOT_TIMEOUT = test_parameters.get("ciot_timeout_min", 0)
        NETWORK_TIMEOUT = test_parameters.get("network_outage_min", 0)
        NETWORK_MODE = test_parameters.get("network_mode", 'both')
        STATION_LABEL = test_parameters.get("station_label", 'B')
        BAND = test_parameters.get("band", 20)
        utils = HATI_Connectivity_Utils()

        # --- Step X: Setup Equipment --- #
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
            if equ.name == "NSTA25MV":
                shaker = equ
        callbox.reset_cells_gain()

        # --- Step Y: Setup Device --- #
        device = self.DUT
        if PRE_CONFIG:
            sync_time = (WAIT_TIME + 1) * 60
            utils._set_profile_preset(device, STATION_LABEL,preset="default")
            utils._execute_shaker_sequence(shaker, STATION_LABEL)
            sleep(sync_time)
            self.logger.info("Test-Execution|Preconfig: Setting back to chosen settings")

        # --- Step 1: Modify network configs --- #
        self.step_start(step_no=1, step_description=f"Modify Network Outage and Band", expected_result=f"-")
        utils._execute_network_outage_sequence(callbox, NETWORK_MODE=NETWORK_MODE, BAND=BAND, outage_mode=self.outage_mode, outage_time=NETWORK_TIMEOUT)
        self.logger.info(f"Test-Execution|Preconfig: Setting Network to outage mode: {self.outage_mode}")
        self.step_end(actual_result=f"Network modified to <ul><li>{NETWORK_MODE} network mode</li> <li>Band {BAND}</li> <li>Outage Mode {self.outage_mode}</li> <li>for {NETWORK_TIMEOUT} minutes</li></ul>", step_verdict="PASSED")

        # --- Step 2: Activate Device --- #
        self.step_start(step_no=2, step_description=f"Using Shaker Station {STATION_LABEL} to trigger motion on the Device", expected_result=f"-")
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        utils._execute_shaker_sequence(shaker, STATION_LABEL)
        shake_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        self.logger.info("Test-Execution|Location: Triggering Shaker")
        self.step_end(actual_result=f"Shaker started at ({start_time_utc}) and stopped successfully at ({shake_time_utc})", step_verdict="PASSED")

        # --- Step 3: Check Location Message --- #
        self.step_start(step_no=3, step_description=f"Check Location message on Device after {WAIT_TIME+CIOT_TIMEOUT} minutes", expected_result=f"Location START and STOP messages received successfully in the backend")
        sleep((WAIT_TIME+2)*60)
        sleep(CIOT_TIMEOUT*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        messages_received, start_msg, stop_msg, keepalive_msg = utils._check_location_messages(backend_messages_t)
        if messages_received:
            self.logger.info("Location messages received successfully")
            self.step_end(actual_result=f"Received location messages successfully. {utils.create_location_event_html(start_msg)} {utils.create_location_event_html(stop_msg)} {utils.create_ka_stop_event_html(keepalive_msg)}", step_verdict="PASSED")

            # --- Step 4: Check Location timestamps --- #
            self.step_start(step_no=4, step_description="Check Location timestamps", expected_result="Location timestamps are valid")
            timestamps_valid, timestamps = utils._check_location_timestamps(start_msg, stop_msg, timestamp_wait_buffer=(CIOT_TIMEOUT/2))
            if timestamps_valid:
                self.logger.info(f"Location timestamps are valid: \nTest_Start_Time: {start_time_utc}\nStart_Msg: {timestamps['start']}\nStop_Msg: {timestamps['stop']}\nTest_End_time: {timestamps['now']}")
                self.step_end(actual_result=f"Location timestamps are valid: <ul><li>Test_Start_Time: {start_time_utc}</li><li>Start_Msg: {timestamps['start']}</li><li>Stop_Msg: {timestamps['stop']}</li><li>Test_End_time: {timestamps['now']}</li></ul>", step_verdict="PASSED")
            else:
                self.logger.info(f"Location timestamps are invalid:  \nTest_Start_Time: {start_time_utc}\nStart_Msg: {timestamps['start']}\nStop_Msg: {timestamps['stop']}\nTest_End_time: {timestamps['now']}")
                self.step_end(actual_result=f"Location timestamps are invalid:  <ul><li>Test_Start_Time: {start_time_utc}</li><li>Start_Msg: {timestamps['start']}</li><li>Stop_Msg: {timestamps['stop']}</li><li>Test_End_time: {timestamps['now']}</li></ul>", step_verdict="FAILED")
        else:
            self.logger.info("Test Failed: No Location message received")
            self.step_end(actual_result="Did not receive a location message", step_verdict="FAILED")

        # --- Step Z: Return to default settings --- #
        callbox.reset_cells_gain()
        
        
class HATI_Connectivity_Periodic_Base(TestScript):
    """Testing the Periodic sequence in an Full service, no netork/internet scenarios

    This testcase uses a standard profile to test a specific network scenario with periodic triggers.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Device is activated
        - Device is in Full service or a Network Outage condition (No Network or No Internet)
    """

    def __init__(self):
        super().__init__()
        self.requirement["DUT"].append("PlatformDevice")
        self.requirement["EQUIPMENT"].append("AMARISOFT")
        self.requirement["EQUIPMENT"].append("NSTA25MV")
        self.n_steps = 2
        self.version = 0.1
        self.outage_mode = None
        if type(self) is HATI_Connectivity_Periodic_Base:
            raise TypeError("HATI_Connectivity_Periodic_Base cannot be instantiated directly")

    def teststeps(self):
        test_parameters = self.params_from_testcfg
        PRE_CONFIG = test_parameters.get("pre_config", False)
        WAIT_TIME = test_parameters.get("downlink_wait_time_min", 5)
        CIOT_TIMEOUT = test_parameters.get("ciot_timeout_min", 0)
        NETWORK_TIMEOUT = test_parameters.get("network_outage_min", 0)
        NETWORK_MODE = test_parameters.get("network_mode", 'both')
        STATION_LABEL = test_parameters.get("station_label", 'B')
        BAND = test_parameters.get("band", 20)
        utils = HATI_Connectivity_Utils()

        # --- Step X: Setup Equipment --- #
        for equ in self.EQUIPMENT:
            if equ.name == "AMARISOFT":
                callbox = equ
            if equ.name == "NSTA25MV":
                shaker = equ
        callbox.reset_cells_gain()

        # --- Step Y: Setup Device --- #
        device = self.DUT
        if PRE_CONFIG:
            sync_time = utils.config_sync_time_min * 60
            utils._set_profile_preset(device, STATION_LABEL,preset="10min_keepalive_test")
            utils._execute_magnet_sequence(shaker, STATION_LABEL)
            sleep(sync_time)
            self.logger.info("Test-Execution|Preconfig: Setting back to chosen settings")

        # --- Step 1: Modify network configs --- #
        self.step_start(step_no=1, step_description=f"Modify Network Outage and Band", expected_result=f"-")
        utils._execute_network_outage_sequence(callbox, NETWORK_MODE=NETWORK_MODE, BAND=BAND, outage_mode=self.outage_mode, outage_time=NETWORK_TIMEOUT)
        self.logger.info(f"Test-Execution|Preconfig: Setting Network to outage mode: {self.outage_mode}")
        self.step_end(actual_result=f"Network modified to <ul><li>{NETWORK_MODE} network mode</li><li>Band {BAND}</li><li>Outage Mode {self.outage_mode}</li><li>for {NETWORK_TIMEOUT} minutes</li></ul>", step_verdict="PASSED")

        # --- Step 2: Check Periodic Message --- #
        self.step_start(step_no=2, step_description=f"Check Periodic message on Device after {WAIT_TIME+CIOT_TIMEOUT} minutes", expected_result=f"Periodic message received successfully in the backend")
        start_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        sleep((WAIT_TIME+2)*60)
        sleep(CIOT_TIMEOUT*60)
        end_time_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        backend_messages_t = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc)
        messages_received, periodic_msg = utils._check_periodic_message(backend_messages_t)
        if messages_received:
            timestamps_valid, timestamps = utils._check_periodic_timestamps(periodic_msg)
            self.logger.info(f"Periodic message received successfully at ({timestamps['periodic']}). Current_Time: {timestamps['now']}")
            self.step_end(actual_result=f"Received periodic messages successfully at: <ul><li>Test_Start_Time: {start_time_utc}</li><li>Periodic_Msg: {timestamps['periodic']}</li><li>Test_End_Time: {timestamps['now']}</li></ul> {utils.create_keep_alive_event_html(periodic_msg)}", step_verdict="PASSED")
        else:
            self.logger.info("Test Failed: No Periodic message received")
            self.step_end(actual_result="Did not receive a periodic message", step_verdict="FAILED")

        # --- Step Z: Return to default settings --- #
        callbox.reset_cells_gain()

class HATI_Connectivity_Activation_ECL_0(HATI_Connectivity_Activation_Base):
    """Testing the Activation sequence in an ECL = 0 or Full Service scenario

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in ECL 0
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Activation_ECL_0"
        self.automation_content = "[Automated] Activation in ECL = 0"
        self.description = "Check Validity of device connection after activating in ECL 0"
        self.test_type = "ecl"
        self.ecl_level = 0
        
          
class HATI_Connectivity_Activation_ECL_1(HATI_Connectivity_Activation_Base):
    """Testing the Activation sequence in an ECL = 1

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in ECL 1
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Activation_ECL_1"
        self.automation_content = "[Automated] Activation in ECL = 1"
        self.description = "Check Validity of device connection after activating in ECL 1"
        self.test_type = "ecl"
        self.ecl_level = 1
        
            
class HATI_Connectivity_Activation_ECL_2(HATI_Connectivity_Activation_Base):
    """Testing the Activation sequence in an ECL = 2

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in ECL 2
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Activation_ECL_2"
        self.automation_content = "[Automated] Activation in ECL = 2"
        self.description = "Check Validity of device connection after activating in ECL 2"
        self.test_type = "ecl"
        self.ecl_level = 2
        
        
class HATI_Connectivity_Activation_No_Network(HATI_Connectivity_Activation_Base):
    """Testing the Activation sequence in a No Network condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a Network Outage condition (No Network)
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Activation_No_Network"
        self.automation_content = "[Automated] Activation in No Network"
        self.description = "Check Validity of device reconnection after activating in No Network"
        self.test_type = "network"
        self.outage_mode = "NO_NETWORK"
        
        
class HATI_Connectivity_Activation_No_Internet(HATI_Connectivity_Activation_Base):
    """Testing the Activation sequence in a No Internet condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a Internet Outage condition (No Internet)
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Activation_No_Internet"
        self.automation_content = "[Automated] Activation in No Internet"
        self.description = "Check Validity of device reconnection after activating in No Internet"
        self.test_type = "network"
        self.outage_mode = "NO_INTERNET"
        
        
class HATI_Connectivity_Location_Full_Service(HATI_Connectivity_Location_Base):
    """Testing the Location sequence in a Full Service condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a Full Service condition
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Location_Full_Service"
        self.automation_content = "[Automated] Location in Full Service"
        self.description = "Check Validity of device reconnection after location event in Full Service"
        self.outage_mode = "FULL_SERVICE"
        
        
class HATI_Connectivity_Location_No_Network(HATI_Connectivity_Location_Base):
    """Testing the Location sequence in a No Network condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a No Network condition
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Location_No_Network"
        self.automation_content = "[Automated] Location in No Network"
        self.description = "Check Validity of device reconnection after location event in No Network"
        self.outage_mode = "NO_NETWORK"
        
        
class HATI_Connectivity_Location_No_Internet(HATI_Connectivity_Location_Base):
    """Testing the Location sequence in a No internet condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a No Internet condition
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Location_No_Internet"
        self.automation_content = "[Automated] Location in No Internet"
        self.description = "Check Validity of device reconnection after location event in No internet"
        self.outage_mode = "NO_INTERNET"
        
        
class HATI_Connectivity_Periodic_Full_Service(HATI_Connectivity_Periodic_Base):
    """Testing the Periodic sequence in a Full Service condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a Full Service condition
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Periodic_Full_Service"
        self.automation_content = "[Automated] Periodic Send in Full Service"
        self.description = "Check Validity of device reconnection periodic event in Full Service"
        self.outage_mode = "FULL_SERVICE"
        
        
class HATI_Connectivity_Periodic_No_Network(HATI_Connectivity_Periodic_Base):
    """Testing the Periodic sequence in a No Network condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a No Network condition
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Periodic_No_Network"
        self.automation_content = "[Automated] Periodic Send in No Network"
        self.description = "Check Validity of device reconnection periodic event in No Network"
        self.outage_mode = "NO_NETWORK"
        
        
class HATI_Connectivity_Periodic_No_Internet(HATI_Connectivity_Periodic_Base):
    """Testing the Periodic sequence in a No internet condition

    Pre-conditions:
        - All pre-conditions from base class
        - Device is in a No Internet condition
    """
    def __init__(self):
        super().__init__()
        self.name = "HATI_Connectivity_Periodic_No_Internet"
        self.automation_content = "[Automated] Periodic Send in No Internet"
        self.description = "Check Validity of device reconnection periodic event in No internet"
        self.outage_mode = "NO_INTERNET"
    