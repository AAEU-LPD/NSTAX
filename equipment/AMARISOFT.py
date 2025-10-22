""" Equipment driver for the network simulator: Amarisoft Classic Callbox.

    Purpose of this module is to control the callbox and its various functionality
    to establish different network parameters and conditions.
"""
import os
import re
import json
from time import sleep
from datetime import datetime, timedelta

from NSTAX.equipment.equipment import Equipment
from NSTAX.interface.remote_interface import RemoteInterface

MAX_RX_GAIN = 60
MAX_TX_POWER = 16
ECL1_RX_GAIN = 40
ECL1_TX_POWER = -20
ECL2_RX_GAIN = 10
ECL2_TX_POWER = -30
NO_NETWORK_GAIN = -100

ws_ports = {
    "mme" : 9000,
    "enb" : 9001,
    # "ue" : 9002,
    # "ims" : 9003,
    # "mbms" : 9004,
    # "n3iwf" : 9005,
    # "license" : 9006,
    # "mon" : 9007,
    # "view" : 9008,
    # "scan" : 9009,
    # "probe" : 9010,
}

linux_cmds = {
    "TIMED_SHUTDOWN": "./test_scripts/timed_shutdown.sh", #in min, loses ssh connection, implement wait + reconnect?
    "TIMED_NO_NETWORK": "./test_scripts/network_autodrop.sh", # in min, spawns as subprocess
    "TIMED_NO_INTERNET": "./test_scripts/packet_autodrop.sh", # in min, spawns as subprocess
    "DISABLE_INTERNET": "./test_scripts/packet_drop.sh", # in min, spawns as subprocess
    "ENABLE_INTERNET": "./test_scripts/packet_restore.sh", # in min, spawns as subprocess
    "DISPLAY_IP_RULES": "iptables -L -n -v", # display rules when internet disabled?
    "RESTART_SERVICES": "systemctl restart lte.service", # restart the enb/mme interfaces
    "SET_ABS_TX_POWER": 'screen -S lte -p 1 -X stuff "abs_tx_power -20 1\n"' # set the absolute tx power on the ENB interface
}

config_cmds = {
    "GET_CONFIG": '{"message":"config_get"}',
    "SET_CONFIG_LOG": '{"message":"config_set","logs":{"bcch":false}}',
    "GET_UE_LIST": '{"message":"ue_get"}',
    "GET_UE_STATS": '{"message":"ue_get","stats":true}',
    "GET_STATS": '{"message":"stats"}',
    "INACTIVATE_CELL": '{"message":"config_set","cells":{"2":{"inactivity_timer":60000}}}',
    "CHANGE_CELL_GAIN": '{"message":"cell_gain","cell_id":2,"gain":-20}',
    # "PLACEHOLDER3": '{"message":"config_set","logs":{"layers":{"PHY":{"level":"debug","max_size":1,"payload":true}},"bcch":false}}',
    # "PLACEHOLDER5": '{"message":"stats", "samples":true}',
    # "PLACEHOLDER6": '{"message":"stats", "samples":true,"rf":true}',
    # "PLACEHOLDER7": '{"message":"stats", "samples":true,"rf":true ,"Initial_delay":0.7}',
    # "PLACEHOLDER10": '{"message":"erab_get"}',
    # "PLACEHOLDER11": '{"message":"qos_flow_get"}',
    "GET_RF_PARAMS": '{"message":"rf"}',
    "SET_RF_PARAMS_RX": '{"message":"rf","rx_gain":40}',
    "SET_RF_PARAMS_TX": '{"message":"rf","tx_gain":10}',
    # "PLACEHOLDER14": '{"message":"rf","tx_gain":70}',
    # "PLACEHOLDER15": '{"message":"rf","rx_gain":50}',
    # "PLACEHOLDER16": '{"message":"rf","rx_agc":-10}',
    # "PLACEHOLDER17": '{"message":"rrc_ue_info_req","enb_ue_id":24,"req_mask":0}',
    # "PLACEHOLDER18": '{"message":"rrc_ue_cap_enquiry","enb_ue_id":27}',
    # "PLACEHOLDER19": '{"message":"rrc_cnx_release","enb_ue_id":27}',
    # "PLACEHOLDER20": '{"message":"dci_bwp_switch","enb_ue_id":45,"dl_bwp_id":0,"ul_bwp_id":0}',
    # "PLACEHOLDER21": '{"message":"x2"}',
    # "PLACEHOLDER22": '{"message":"s1"}',
    # "PLACEHOLDER23": '{"message":"s1connect"}',
    # "PLACEHOLDER24": '{"message":"s1disconnect"}',
    # "PLACEHOLDER25": '{"message":"ng"}',
    # "PLACEHOLDER26": '{"message":"ngconnect"}',
    # "PLACEHOLDER27": '{"message":"ngdisconnect"}',
    # "PLACEHOLDER28": '{"message":"sib_set","cells":{"1":{"sib1":{"p_max":20}}}}',
    # "PLACEHOLDER29": '{"message":"page_ue","cell_id":[1],"type":"normal","cn_domain":"ps","imsi":"001010123456789"}',
    # "PLACEHOLDER30": '{"message":"rrc_cnx_reconf","enb_ue_id":1,"dl_bwp_id":1,"ul_bwp_id":1}',
    # "PLACEHOLDER31": '{"message":"dci_bwp_switch","enb_ue_id":1,"ul_bwp_id":1}',
    # "PLACEHOLDER32": '{"message":"dci_bwp_switch","enb_ue_id":1,"dl_bwp_id":1}',
    # "PLACEHOLDER33": '{"message":"trx_iq_dump", "duration":5000 , "rx_filename":"\\tmp\\rx.bin", "tx_filename":"\\tmp\\tx.bin"}',
    # "PLACEHOLDER34": '{"message":"pdcch_order_prach", "enb_ue_id":1 }',
    # "PLACEHOLDER35": '{"message": "config_set","cells": {"1": {"rrc_procedure_filter":{"rrc_connection_request":"reject"}}}}',
    # "PLACEHOLDER36": '{"message":"config_set","cells":{"1":{"pdsch_mcs":4}}}',
    # "PLACEHOLDER37": '{"message":"config_set","cells":{"1":{"force_dl_schedule":true}}}',
    # "PLACEHOLDER38": '{"message":"config_set","cells":{"1":{"pdsch_fixed_rb_alloc":true,"pdsch_fixed_rb_start":0,"pdsch_fixed_l_crb":20}}}',
}


class AMARISOFT(Equipment):
    """Equipment class for Amarisoft Classic Callbox.

    :param host_ip: IP address of the Callbox connected to lab net
    :type host_ip: str
    """
    def __init__(self, host_ip):
        super().__init__("AMARISOFT", version=0.1)
        self.host_ip = host_ip        # IP Port for the Callbox
        self.interface = None

    def connect(self):
        """Connect to the Callbox"""
        if self.is_connected():
            self.disconnect()
        #Connect to interface (user,pass,ip address)
        self.interface = RemoteInterface("root","toor", self.host_ip)
        try:
            self.interface.connect()
        except self.interface.CouldNotConnectError as err:
            raise self.CouldNotConnectError("Error connecting to SSH interface via address: {}".format(self.host_ip), orig_error_msg=str(err))
        self.connected = True

    def disconnect(self):
        """Disconnect the Callbox"""
        # Send command (exit)
        if self.is_connected():
            self.interface.disconnect()
        self.connected = False

    def _send_command(self, command, interface_port=9000, is_ssh_cmd=True, read_output=False):
        """Send Amarisoft command"""
        response = self.interface.send_command(command, interface_port, is_ssh_cmd, read_output)
        return response
    
    ### GENERIC CONTROL FUNCTIONS ###
    def restart_services(self):
        """Restart the LTE services on the callbox

        :return: returns the reply
        :rtype: str
        """
        command = linux_cmds.get("RESTART_SERVICES")
        reply = self._send_command(command, read_output=True)
        return reply

    ### GENERIC GET FUNCTIONS
    def config_get(self, interface_name):
        """Get configuration of the callbox

        :param interface_name: ENB/MME interface selection
        :type interface_name: string
        :return: config json from the callbox
        :rtype: str
        """
        command = config_cmds.get("GET_CONFIG")
        ws_port = ws_ports.get(f"{interface_name}")
        config = self._send_command(command, ws_port, is_ssh_cmd=False)
        return config
        
    def ue_get(self, interface_name="mme"):
        """Get connected UEs

        :param interface_name: ENB/MME interface selection, defaults to "mme"
        :type interface_name: str, optional
        :return: config json from the callbox
        :rtype: str
        """
        command = config_cmds.get("GET_UE_LIST")
        ws_port = ws_ports.get(f"{interface_name}")
        config = self._send_command(command, ws_port, is_ssh_cmd=False)
        return config
    
    def ip_rules_get(self):
        """Get current IP rules set on the callbox

        :return: returns the reply
        :rtype: str
        """
        command = linux_cmds.get("DISPLAY_IP_RULES")
        reply = self._send_command(command, read_output=True)
        return reply
    
    ### CELL RELATED FUNCTIONS
    def get_cells(self, cell_type, cell_id="", interface_name="enb"):
        """Get the cell info from the callbox

        :param cell_type: type of cell to fetch ('nbiot' or 'catm1')
        :type cell_type: str
        :param cell_id: specific cell to fetch based on cell ID, defaults to ""
        :type cell_id: str, optional
        :param interface_name: ENB/MME interface selection, defaults to "enb"
        :type interface_name: str, optional
        :return: cell(s) information
        :rtype: dict or list
        """
        config = self.config_get(interface_name)
        if cell_type == "nbiot":
            cells = json.loads(config)['nb_cells']
        elif cell_type == "catm1":
            cells = json.loads(config)['cells']   
        else:
            print(f"Error: Unsupported cell type '{cell_type}'.")
            return None
        if cell_id != "":
            cells = cells[cell_id]
        return cells
    
    def get_rf_params(self, interface_name="enb"):
        """Get the radio gain params from the callbox

        :param interface_name: ENB/MME interface selection, defaults to "enb"
        :type interface_name: str, optional
        :return: config json from the callbox
        :rtype: str
        """
        command = config_cmds.get("GET_RF_PARAMS")
        ws_port = ws_ports.get(f"{interface_name}")
        config = self._send_command(command, ws_port, is_ssh_cmd=False)
        return config
    
    def get_cell_ids(self, cell_type):
        """Get all cells currently available in the callbox

        :param cell_type: type of cell to fetch ('nbiot' or 'catm1')
        :type cell_type: str
        :return: array of cells
        :rtype: list
        """
        cells = self.get_cells(cell_type=cell_type)
        cell_ids = list(cells.keys())
        return cell_ids
    
    def get_valid_cell_id_locations(self, interface_name="enb"):
        """Get the cell ID numbers that are available in the callbox

        :param interface_name:  ENB/MME interface selection, defaults to "enb"
        :type interface_name: str, optional
        :return: array of cell ID numbers
        :rtype: list
        """
        locations = []
        config = self.config_get(interface_name)
        enb_id = json.loads(config)['global_enb_id']["enb_id"]
        cell_ids = self.get_cell_ids('nbiot')
        for cell_id in cell_ids:
            id_string = format(int(cell_id), '#04x')
            location = int(hex(enb_id) + id_string[2:], 16)
            locations.append(str(location))
        return locations

    def get_cell_gain(self, cell_id, cell_type):
        """Get the gain set for a particular cell

        :param cell_id: the cell id/index of the cell
        :type cell_id: str
        :param cell_type: type of cell to fetch ('nbiot' or 'catm1')
        :type cell_type: str
        :return: gain value of the cell
        :rtype: int
        """
        cells = self.get_cells(cell_type=cell_type, cell_id=cell_id)
        cell_gain = cells['gain']
        return cell_gain

    def set_cell_gain(self, cell_id, gain_value, interface_name="enb"):
        """Set the gain set for a particular cell

        :param cell_id: the cell id/index of the cell
        :type cell_id: str
        :param gain_value: gain value of the cell
        :type gain_value: int
        :param interface_name: ENB/MME interface selection, defaults to "enb"
        :type interface_name: str, optional
        :return: returns the reply
        :rtype: str
        """
        min_gain = -100
        max_gain = 0
        if gain_value > max_gain:
            gain_value = max_gain
        if gain_value < min_gain:
            gain_value = min_gain
        command = f'{{"message":"cell_gain","cell_id":{cell_id},"gain":{gain_value}}}'
        ws_port = ws_ports.get(f"{interface_name}")
        reply = self._send_command(command, ws_port, is_ssh_cmd=False)
        return reply
    
    def reset_cells_gain(self):
        """Reset the gain value of all cells to default(0)
        """
        gain_value = 0.0
        cell_ids = self.get_cell_ids('nbiot') + self.get_cell_ids('catm1')
        for cell in cell_ids:
            self.set_cell_gain(cell, gain_value)
            
    def get_tx_gain(self):
        """Get the tx_gain value set on the callbox

        :return: tx_gain values
        :rtype: array
        """
        rf_params = self.get_rf_params()
        rx_gain = json.loads(rf_params)['tx_gain']
        return rx_gain
    
    def get_rx_gain(self, interface_name="enb"):
        """Get the rx_gain value set on the callbox

        :return: rx_gain values
        :rtype: array
        """
        rf_params = self.get_rf_params()
        rx_gain = json.loads(rf_params)['rx_gain']
        return rx_gain
    
    def set_tx_gain(self, gain_value, interface_name="enb"):
        """Set the tx_gain value on the callbox

        :param gain_value: gain value of the cell
        :type gain_value: int
        :param interface_name: ENB/MME interface selection, defaults to "enb"
        :type interface_name: str, optional
        :return: returns the reply
        :rtype: str
        """
        min_tx_gain = 43.2
        max_tx_gain = 89.3
        if gain_value > max_tx_gain:
            gain_value = max_tx_gain
        if gain_value < min_tx_gain:
            gain_value = min_tx_gain
        command = f'{{"message":"rf","tx_gain":{gain_value}}}'
        ws_port = ws_ports.get(f"{interface_name}")
        reply = self._send_command(command, ws_port, is_ssh_cmd=False)
        return reply
            
    def set_rx_gain(self, gain_value, interface_name="enb"):
        """Set the rx_gain value on the callbox

        :param gain_value: gain value of the cell
        :type gain_value: int
        :param interface_name: ENB/MME interface selection, defaults to "enb"
        :type interface_name: str, optional
        :return: returns the reply
        :rtype: str
        """
        min_rx_gain = 0
        max_rx_gain = 70
        if gain_value > max_rx_gain:
            gain_value = max_rx_gain
        if gain_value < min_rx_gain:
            gain_value = min_rx_gain
        command = f'{{"message":"rf","rx_gain":{gain_value}}}'
        ws_port = ws_ports.get(f"{interface_name}")
        reply = self._send_command(command, ws_port, is_ssh_cmd=False)
        return reply
    
    def set_tx_gain_ch(self, channel, gain_value):
        """Set the tx_gain value on the callbox for a specified channel

        :param channel: tx channel to modify
        :type channel: int
        :param gain_value: gain value of the channel
        :type gain_value: int
        :return: returns the reply
        :rtype: str
        """
        interface_name="enb"
        min_tx_gain = 43.2
        max_tx_gain = 89.3
        if gain_value > max_tx_gain:
            gain_value = max_tx_gain
        if gain_value < min_tx_gain:
            gain_value = min_tx_gain
        command = f'{{"message":"rf","tx_gain":{gain_value},"tx_channel_index":{channel}}}'
        ws_port = ws_ports.get(f"{interface_name}")
        reply = self._send_command(command, ws_port, is_ssh_cmd=False)
        return reply
    
    def set_rx_gain_ch(self, channel, gain_value):
        """Set the rx_gain value on the callbox for a specified channel

        :param channel: rx channel to modify
        :type channel: int
        :param gain_value: gain value of the channel
        :type gain_value: int
        :return: returns the reply
        :rtype: str
        """
        interface_name="enb"
        min_rx_gain = 0
        max_rx_gain = 70
        if gain_value > max_rx_gain:
            gain_value = max_rx_gain
        if gain_value < min_rx_gain:
            gain_value = min_rx_gain
        command = f'{{"message":"rf","rx_gain":{gain_value},"rx_channel_index":{channel}}}'
        ws_port = ws_ports.get(f"{interface_name}")
        reply = self._send_command(command, ws_port, is_ssh_cmd=False)
        return reply
    
    def set_abs_tx_power(self, gain_value):
        """Set the absolute tx power value on the callbox

        :param channel: tx channel to modify
        :type channel: int
        :param gain_value: gain value of the channel
        :type gain_value: int
        """
        min_tx_power = -73.5
        max_tx_power = 16
        if gain_value > max_tx_power:
            gain_value = max_tx_power
        if gain_value < min_tx_power:
            gain_value = min_tx_power
        command = f'screen -S lte -p 1 -X stuff "abs_tx_power {gain_value}\n"'
        self._send_command(command)
    
    def set_abs_tx_power_ch(self, channel, gain_value):
        """Set the absolute tx power value on the callbox for a specified channel

        :param channel: tx channel to modify
        :type channel: int
        :param gain_value: gain value of the channel
        :type gain_value: int
        """
        min_tx_power = -73.5
        max_tx_power = 16
        if gain_value > max_tx_power:
            gain_value = max_tx_power
        if gain_value < min_tx_power:
            gain_value = min_tx_power
        command = f'screen -S lte -p 1 -X stuff "abs_tx_power {gain_value} {channel}\n"'
        self._send_command(command)
        
    def trigger_no_internet(self, duration_min, start_time=datetime.now()):
        # PYTHON THREAD vs AMARISOFT SUBPROCESS -> Subprocess is better for running testcases incase of disruption/losing connection
        # BASH SCRIPTS vs MANUAL COMMANDS -> bashscripts work fine with a subprocess
        """Trigger a period of internet disconnection in the callbox

        :param duration_min: time in mins 
        :type duration_min: int
        :param start_time: timestamp, defaults to datetime.now()
        :type start_time: str, optional
        """
        delay = round((start_time - datetime.now()).total_seconds())
        if delay > 0:
            print(f"Scheduled no internet to run in {delay} seconds.")
            sleep(delay)
        command = linux_cmds.get("TIMED_NO_INTERNET") + f" {duration_min} &"
        self._send_command(command)
    
    # def trigger_no_internet(self, duration_min):
    #     callbox._disable_internet()
    #     sleep(duration_min * 60)
    #     callbox._enable_internet()
    
    def trigger_no_network(self, duration_min, start_time=datetime.now()):
        """Trigger a period of network disconnection in the callbox

        :param duration_min: time in mins 
        :type duration_min: int
        :param start_time: timestamp, defaults to datetime.now()
        :type start_time: str, optional
        """
        delay = round((start_time - datetime.now()).total_seconds())
        if delay > 0:
            print(f"Scheduled no network to run in {delay} seconds.")
            sleep(delay)
        cell_ids = self.get_cell_ids('nbiot') + self.get_cell_ids('catm1')
        cell_ids_str = " ".join(str(cell_id) for cell_id in cell_ids)
        command = linux_cmds.get("TIMED_NO_NETWORK") + f" {duration_min} {cell_ids_str} &"
        self._send_command(command)
    
    def trigger_shutdown(self, duration_min, start_time=datetime.now()):
        """Trigger a period of shutdown in the callbox

        :param duration_min: time in mins 
        :type duration_min: int
        :param start_time: timestamp, defaults to datetime.now()
        :type start_time: str, optional
        """
        delay = round((start_time - datetime.now()).total_seconds())
        if delay > 0:
            print(f"Scheduled shutdown to run in {delay} seconds. Note: SSH will be disconnected!")
            sleep(delay)
        command = linux_cmds.get("TIMED_SHUTDOWN") + f" {duration_min}"
        self._send_command(command)
        
    def trigger_ecl_0_all_cells(self):
        """ Sets the receiver gain and absolute transmit power to their maximum values for all cells."""
        self.set_rx_gain(MAX_RX_GAIN)
        self.set_abs_tx_power(MAX_TX_POWER)
        
    def trigger_ecl_1_all_cells(self):
        """Configures all cells to ECL1 by setting RX gain and absolute TX power."""
        self.set_rx_gain(ECL1_RX_GAIN)
        self.set_abs_tx_power(ECL1_TX_POWER)

    def trigger_ecl_2_all_cells(self):
        """Configures all cells to ECL2 by setting RX gain and absolute TX power."""
        self.set_rx_gain(ECL2_RX_GAIN)
        self.set_abs_tx_power(ECL2_TX_POWER)
    
    def trigger_ecl_0(self, channel):
        """Configures the specified channel with maximum RX gain and TX power.

        :param channel: Channel index to configure
        :type channel: int
        """
        self.set_rx_gain_ch(channel, MAX_RX_GAIN)
        self.set_abs_tx_power_ch(channel, MAX_TX_POWER)
        
    def trigger_ecl_1(self, channel):
        """Configures the specified channel with ECL1 RX gain and TX power settings.

        :param channel: Channel index to configure
        :type channel: int
        """
        self.set_rx_gain_ch(channel, ECL1_RX_GAIN)
        self.set_abs_tx_power_ch(channel, ECL1_TX_POWER)
        
    def trigger_ecl_2(self, channel):
        """Configures the specified channel with ECL2 RX gain and TX power settings.

        :param channel: Channel index to configure
        :type channel: int
        """
        self.set_rx_gain_ch(channel, ECL2_RX_GAIN)
        self.set_abs_tx_power_ch(channel, ECL2_TX_POWER)
    
    def _disable_internet(self):
        """Trigger a packet drop script to disable internet

        :return: returns the reply
        :rtype: str
        """
        command = linux_cmds.get("DISABLE_INTERNET")
        reply = self._send_command(command)
        return reply
    
    def _enable_internet(self):
        """Trigger a packet restore script to re-enable internet

        :return: returns the reply
        :rtype: str
        """
        command = linux_cmds.get("ENABLE_INTERNET")
        reply = self._send_command(command)
        return reply
    
    ### ENB CONFIG FUNCTIONS
    def _get_band_frequencies(self, band1, band2, band3):
        """
        Returns the downlink frequency values corresponding to the provided LTE band numbers,
        with adjustments for overlapping bands.

        :available bands: 1, 2, 3, 4, 5, 8, 12, 13, 20, 28

        :param band1: The first LTE band number.
        :type band1: int
        :param band2: The second LTE band number.
        :type band2: int
        :param band3: The third LTE band number.
        :type band3: int
        :return: A tuple of three integers or None values representing the downlink frequencies
             for band1, band2, and band3, respectively. If a band number is not found in the
             mapping, its frequency will be None.
        :rtype: tuple
        :notes:
            - The function uses a predefined mapping of LTE band numbers to their corresponding
              downlink EARFCN (frequency) values.
            - If the same band number appears more than once among the inputs, the frequency for
              the later occurrence(s) is increased by 50 to avoid overlap.
            - The function does not validate whether the provided band numbers are valid LTE bands
              beyond the mapping.
        """
        
        # Mapping of LTE band numbers to their corresponding downlink EARFCN (frequency) values
        band_to_frequency = {
        1: 250,
        2: 850,
        3: 1525,
        4: 2125,
        5: 2475,
        8: 3575,
        12: 5045,
        13: 5180,
        20: 6250,
        28: 9385,
        }
        # Map each band to its frequency, or None if not found
        bands = [band1, band2, band3]
        freqs = [band_to_frequency.get(b, None) for b in bands]
        # Adjust overlapping bands by adding +50 to the frequency if bands are the same
        for i in range(len(bands)):
            for j in range(i + 1, len(bands)):
                if bands[i] == bands[j]:
                    # Only add +50 to the later occurrence(s)
                    if freqs[j] is not None:
                        freqs[j] += 50
        # Unpack the possibly adjusted frequencies
        band1_freq, band2_freq, band3_freq = freqs
        return band1_freq, band2_freq, band3_freq
    
    def modify_enb_config(self, network_mode, band1=20, band2=20, band3=20, coverage_levels=False):
        """
        Modifies the eNB configuration file based on the specified network mode, frequency bands, and coverage levels.

        :param network_mode: The network mode to configure. Must be one of 'nbiot', 'catm1', or 'both'.
        :type network_mode: str
        :param band1: The LTE band for cell 1. Defaults to 20.
        :type band1: int, optional
        :param band2: The LTE band for cell 2. Defaults to 20.
        :type band2: int, optional
        :param band3: The LTE band for cell 3. Defaults to 20.
        :type band3: int, optional
        :param coverage_levels: Whether to enable enhanced coverage levels (ECL for NB-IoT, Coverage Level 2 for Cat-M1). Defaults to False.
        :type coverage_levels: bool, optional

        :return: None
        :rtype: None

        :raises: Prints an error and returns None if the network mode is unsupported or the template file is not found.
        """

        # Select config file from template and read out the settings
        if network_mode == 'nbiot':
            file_name = "enb-nbiot-3-cells-b20.cfg"
        elif network_mode == 'catm1':
            file_name = "enb-catm1-3-cells-b20.cfg"
        elif network_mode == 'both':
            file_name = "enb-both-3-cells-b20.cfg"
        else:
            print(f"Error: Unsupported network mode '{network_mode}'.")
            raise ValueError("Unsupported network mode")
        file_path = f"static/amarisoft_configs/{file_name}"
        if not os.path.exists(file_path):
            print(f"Error: The local file '{file_path}' was not found.")
            raise FileNotFoundError
        with open(file_path, 'r', encoding='utf-8') as f:
            enb_config = f.read()
        # Configure settings from params
        band1_freq, band2_freq, band3_freq = self._get_band_frequencies(band1, band2, band3)
        enb_config = re.sub(r'#define LTE_DL_EARFCN_1.*', f'#define LTE_DL_EARFCN_1 {band1_freq} // Set to band {band1}', enb_config)
        enb_config = re.sub(r'#define LTE_DL_EARFCN_2.*', f'#define LTE_DL_EARFCN_2 {band2_freq} // Set to band {band2}', enb_config)
        enb_config = re.sub(r'#define LTE_DL_EARFCN_3.*', f'#define LTE_DL_EARFCN_3 {band3_freq} // Set to band {band3}', enb_config)
        if network_mode == 'nbiot':
            ce_level_value = 1 if coverage_levels else 0
            enb_config = re.sub(r'#define ALL_CE_LEVELS.*', f'#define ALL_CE_LEVELS {ce_level_value} // ECL Enabled: {coverage_levels}', enb_config)
        if network_mode == 'catm1':
            coverage_level_value = 2 if coverage_levels else 1
            enb_config = re.sub(r'#define N_COVERAGE_LEVEL.*', f'#define N_COVERAGE_LEVEL {coverage_level_value} // Coverage Level 2 Enabled: {coverage_levels}', enb_config)
        if network_mode == 'both':
            ce_level_value = 1 if coverage_levels else 0
            coverage_level_value = 2 if coverage_levels else 1
            enb_config = re.sub(r'#define ALL_CE_LEVELS.*', f'#define ALL_CE_LEVELS {ce_level_value} // ECL Enabled: {coverage_levels}', enb_config)
            enb_config = re.sub(r'#define N_COVERAGE_LEVEL.*', f'#define N_COVERAGE_LEVEL {coverage_level_value} // Coverage Level 2 Enabled: {coverage_levels}', enb_config)
        # Check if the remote config already matches the new content
        check_command = "cat /root/enb/config/enb.cfg"
        current_config = self._send_command(check_command, read_output=True)
        if current_config == enb_config:
            was_updated = False
        else:
            # Save the modified config to the remote location
            command = f"echo '{enb_config}' > /root/enb/config/enb.cfg"
            self._send_command(command)
            was_updated = True
        return was_updated

    def save_enb_config_from_default(self, file_name):
        """
        Save the default eNB configuration file to the remote Amarisoft callbox.

        This method reads a local configuration template file (from the static/amarisoft_configs directory)
        and writes its contents to the remote callbox at /root/enb/config/enb.cfg using an SSH command.

        :param file_name: Name of the configuration template file to use (e.g., "enb-nbiot-3-cells-b20.cfg").
        :type file_name: str

        :return: None if successful, or prints an error and returns None if the file is not found.
        :rtype: None

        :raises: Prints an error if the local configuration file does not exist.
        """
        file_path = f"static/amarisoft_configs/{file_name}"
        if not os.path.exists(file_path):
            print(f"Error: The local file '{file_path}' was not found.")
            raise FileNotFoundError
        with open(file_path, 'r', encoding='utf-8') as f:
            enb_config = f.read()
        command = f"echo '{enb_config}' > /root/enb/config/enb.cfg"
        self._send_command(command)
        
    def change_network_bands(self, network_mode, band1, band2, band3, coverage_levels=False):
        """
        Change the network bands and optionally enable coverage levels.

        This method updates the eNB configuration on the Amarisoft callbox to use the specified LTE bands
        and coverage level settings. It modifies the configuration file based on the selected network mode
        ('nbiot', 'catm1', or 'both'), sets the downlink frequencies for up to three cells, and enables or disables
        enhanced coverage levels as requested. After updating the configuration, it restarts the LTE services
        to apply the changes.

        :param network_mode: The network mode to configure. Must be one of 'nbiot', 'catm1', or 'both'.
        :type network_mode: str
        :param band1: The LTE band for cell 1.
        :type band1: int
        :param band2: The LTE band for cell 2.
        :type band2: int
        :param band3: The LTE band for cell 3.
        :type band3: int
        :param coverage_levels: Whether to enable enhanced coverage levels (ECL for NB-IoT, Coverage Level 2 for Cat-M1). Defaults to False.
        :type coverage_levels: bool, optional

        :return: None
        :rtype: None

        :raises: Prints an error and returns None if the network mode is unsupported or the template file is not found.
        """
        file_updated = self.modify_enb_config(network_mode, band1, band2, band3, coverage_levels)
        if file_updated:
            self.restart_services()
        
# --- Sample Runs --- #       
def sample_run_get_config(callbox):
    """Sample: Get and print ENB and MME config, and UE list."""
    config = callbox.config_get("enb")
    print("ENB Config:", config)
    config = callbox.config_get("mme")
    print("MME Config:", config)
    config = callbox.ue_get()
    print("UE List:", config)

def sample_run_get_ip_rules(callbox):
    """Sample: Get and print IP rules table."""
    ip_table = callbox.ip_rules_get()
    print("IP Rules Table:", ip_table)

def sample_run_trigger_no_internet(callbox, timeout_hr=1, start_time=None):
    """Sample: Trigger no internet for a given number of hours."""
    if start_time is None:
        start_time = datetime.now()
    duration_min = timeout_hr * 60
    callbox.trigger_no_internet(duration_min, start_time)
    sleep((duration_min+1)*60)

def sample_run_trigger_no_network(callbox, timeout_hr=1, start_time=None):
    """Sample: Trigger no network for a given number of hours."""
    if start_time is None:
        start_time = datetime.now()
    duration_min = timeout_hr * 60
    duration_min = 1 # For testing, set to 10 mins
    callbox.trigger_no_network(duration_min, start_time)
    sleep((duration_min+1)*60)

def sample_run_trigger_shutdown(callbox, duration_min=5):
    """Sample: Trigger shutdown for a given number of minutes."""
    print(callbox.trigger_shutdown(duration_min))
    sleep((duration_min+1)*60)

def sample_run_change_cell_gain(callbox, cell_type='nbiot', gain_value=-20):
    """Sample: Change cell gain for all cells of a type and print."""
    cells = callbox.get_cell_ids(cell_type)
    for cell in cells:
        callbox.set_cell_gain(cell, gain_value)
        config = callbox.get_cell_gain(cell, cell_type)
        print(f"Cell {cell} gain:", config)
    callbox.reset_cells_gain()

def sample_run_rx_gain(callbox, channel=2, gain_value=40):
    """Sample: Set and get RX gain for a channel."""
    config = callbox.get_rx_gain()
    print("Current RX Gain:", config)
    config = callbox.set_rx_gain_ch(channel, gain_value)
    print(f"Set RX Gain Channel {channel}:", config)
    config = callbox.get_rx_gain()
    print("Updated RX Gain:", config)

def sample_run_abs_tx_power(callbox, channel=2, gain_value=-20):
    """Sample: Set absolute TX power for a channel."""
    callbox.set_abs_tx_power_ch(channel, gain_value)

def sample_run_ecl_levels(callbox, channel=2, duration_min=10):
    """Sample: Trigger ECL levels for all cells and a specific channel."""
    # callbox.trigger_ecl_0_all_cells()
    # callbox.trigger_ecl_1_all_cells()
    callbox.trigger_ecl_2_all_cells()
    sleep(duration_min * 60)
    # callbox.trigger_ecl_2(channel)
    # callbox.trigger_ecl_1(channel)
    callbox.trigger_ecl_0(channel)

def sample_run_get_cell_id_locs(callbox):
    """Sample: Get and print valid cell ID locations."""
    config = callbox.get_valid_cell_id_locations()
    print("Valid Cell ID Locations:", config)

def sample_run_save_enb_configs(callbox):
    """Sample: Save default ENB configs and restart services."""
    callbox.save_enb_config_from_default("enb-nbiot-3-cells-b20.cfg")
    callbox.save_enb_config_from_default("enb-both-3-cells-b20.cfg")
    callbox.restart_services()
    sleep(10)
    callbox.save_enb_config_from_default("enb-catm1-3-cells-b20.cfg")

def sample_run_change_network_bands(callbox):
    """Sample: Change network bands and optionally enable coverage levels."""
    # callbox.change_network_bands('nbiot', 1, 4, 20, coverage_levels=False)
    # callbox.change_network_bands('nbiot', 1, 4, 20, coverage_levels=False)
    callbox.change_network_bands('both', 20, 20, 20, coverage_levels=False)
    
def sample_run_cell_gain_handling(callbox, cell_type='catm1'):
    """Sample: Reset all cell gains and optionally set all cell gains to -100 for the given cell type."""
    callbox.reset_cells_gain()
    cells = callbox.get_cell_ids(cell_type)
    for cell in cells:
        callbox.set_cell_gain(cell, -100)
        config = callbox.get_cell_gain(cell, cell_type)
        print(config)

if __name__ == "__main__":
    START_TIME = datetime.now() + timedelta(seconds=10)
    TRIGGER_DURATION = 10 # in mins
    # Example run
    callbox = AMARISOFT("10.51.16.6")   # Connect to the callbox with the specifed IP address
    callbox.connect()
    
    # Example usage in main:
    # sample_run_get_config(callbox)
    # sample_run_get_ip_rules(callbox)
    # sample_run_trigger_no_internet(callbox, timeout_hr=1, start_time=START_TIME)
    # sample_run_trigger_no_network(callbox)
    # sample_run_trigger_shutdown(callbox, duration_min=5)
    # sample_run_change_cell_gain(callbox, cell_type='nbiot', gain_value=-20)
    # sample_run_rx_gain(callbox, channel=2, gain_value=40)
    # sample_run_abs_tx_power(callbox, channel=2, gain_value=-20)
    # sample_run_ecl_levels(callbox, channel=2, duration_min=TRIGGER_DURATION)
    # sample_run_get_cell_id_locs(callbox)
    # sample_run_save_enb_configs(callbox)
    sample_run_change_network_bands(callbox)
    # sample_run_cell_gain_handling(callbox, cell_type='catm1')

    callbox.disconnect()