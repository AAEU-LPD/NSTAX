
import serial
import serial.tools.list_ports
import time
import sys
import datetime
import re
 
import argparse
from time import sleep
import traceback

class DualOutput:
    def __init__(self, terminal, log_file):
        self.terminal = terminal
        self.log_file = log_file

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

TR_TIMEOUT = 20 # global timeout in seconds
TR_WAIT = 0.6   # wait answer form modem in seconds
TR_WAIT_LONG = 10   # wait answer form modem in seconds
debug=0


def custom_unraisablehook(unraisable):
    print("Unraisable exception:", unraisable.exc_value)
    traceback.print_exception(unraisable.exc_type, unraisable.exc_value, unraisable.exc_traceback)


def timehr():
    # return curren PC time with µs resolution
    return time.time_ns() /1e9


def time_stamp():
    # return curren PC time with µs resolution
    nowtime = time.time_ns() /1e9
    return datetime.datetime.fromtimestamp(nowtime)

def time_st_pres():
    # return current PC time with µs resolution (Linux compatible)
    nowtime = time.time()
    return datetime.datetime.fromtimestamp(nowtime)

def hex2signedByte(hex_value):
    # Convert hex to integer
    int_value = int(hex_value, 16)
    # Check if the integer is greater than 127 (0x7F), which is the max value for 8-bit signed integers
    if int_value > 0x7F:
        # Convert to signed by subtracting 256
        int_value -= 0x100
    
    return int_value

def hex2signedI16(hex_value):
    # Convert hex to integer
    int_value = int(hex_value, 16)
    # Check if the integer is greater than 127 (0x7F), which is the max value for 8-bit signed integers
    if int_value > 0x7FFF:
        # Convert to signed by subtracting 256
        int_value -= 0x10000
    
    return int_value


def print_tsp(string2print):
     print(f"({time_st_pres()}){string2print}")


def send_at_command(serial_port, command):
    """
    Send an AT command to the serial port and return the response.

    :param serial_port: The serial port object.
    :param command: The AT command to send.
    :param timeout: Time to wait for a response (in seconds).
    :return: The response from the serial device.
    """
    # Ensure command ends with a carriage return and newline
    command += "\r\n"
    print_tsp(command)
    # Send the command
    serial_port.write(command.encode('utf-8'))
    

def receive_response(serial,timeout_rec):
    response = ""
    timer_receive = timehr()+timeout_rec
    i=0
    j=0
    while ((timehr() < timer_receive) & (serial.in_waiting == 0)) : 
        time.sleep(0.01)
        i=i+1
    while (serial.in_waiting > 0) : 
        response = response + serial.read_all().decode('utf-8').strip()
        time.sleep(0.01)
        j=j+1
    #print(f"wait={i}, rec={j}, resp {response}\r\n")
    return response

def receive_line(serial,timeout_rec):
    response = ""
    timer_receive = timehr()+timeout_rec
    i=0
    j=0
    while ((timehr() < timer_receive) & (serial.in_waiting == 0)) : 
        time.sleep(0.01)
        i=i+1
    timer_receive = timehr()+timeout_rec
    endline = False
    while ((timehr() < timer_receive) & (endline == False)) : 
        if (serial.in_waiting > 0) : 
            response = response + serial.read_all().decode('utf-8')
            if (response[-1]==("\n")) | (response[-1]==("\r")):
                endline = True
                if(debug==1) : print(f"<{response}> end of line detected\r\n") 
        else :
            time.sleep(0.01)
            j=j+1
            
    if(debug==1) : print(f"wait={i}, rec={j}, resp {response}\r\n")
    return response


def revert_nibbles(hex_string):
    # Ensure the hex string length is even
    if len(hex_string) % 2 != 0:
        raise ValueError("Hex string length must be even.")
    
    # Initialize the result string
    result = ""
    
    # Loop through the hex string two characters at a time
    for i in range(0, len(hex_string), 2):
        byte = hex_string[i:i+2]
        # Swap the nibbles within the byte
        swapped_byte = byte[1] + byte[0]
        result += swapped_byte
    
    return result

def decode_steng(input_steng) :
    #"#STENG: SF=001F5C56,CID=00000012,ECID=09BA28D0,SRV1=FFC118CA,SRV2=FFF0FFB2,MODE=0002F63C,ECL=00003860,TXP=0201EAEA,PLMN=0002F801,TAC=0000C3AB,EDRX=0000000B,PSM=00003E00,MIC=0000DE78,NGHB=00000000,NGH1=00000000,NGH2=00000000"

    # Remove the prefix
    input_steng = input_steng.replace("#STENG:", "")
    position = input_steng.find("#SLEEP")
    # Check if the substring is found
    if position != -1:
        # Slice the string from the start up to the position of the substring
        input_steng = input_steng[:position]

    # Split the string into key-value pairs
    pairs = input_steng.split(',')

    # Create a dictionary to store the separated data
    data_dict = {}

    # Loop through the pairs and split them into key and value
    for pair in pairs:
        key, value = pair.split('=')
        if (key == "SF") | (key == "ATM") | (key == "STIM"):
            value = str(int(value, 16)/1000)+"s"
            data_dict[key] = value
        elif (key == "CID") :
            # Convert CID from hex to decimal
            value = str(int(value, 16))
            data_dict[key] = value
        elif (key == "ECID") :
            data_dict[key] = value
        elif key == "SRV1":
            # Split SRV1 into two 16-bit values
            high_16bit = value[:4]
            low_16bit = value[4:]
            rssi = hex2signedI16(high_16bit)
            Channel = str(int(low_16bit, 16))
            # Store the split values in the dictionary
            data_dict["RSSI"] = rssi
            data_dict["CHANNEL"] = Channel
        elif key == "SRV2":
            high_16bit = value[:4]
            low_16bit = value[4:]
            rsrq = hex2signedI16(high_16bit)
            rsrp = hex2signedI16(low_16bit)
            data_dict["RSRP"] = rsrp
            data_dict["RSRQ"] = rsrq
        elif key == "MODE":
            mapping = {
                    0: "In-Band Same PCI",
                    1: "In-Band different PCI",
                    2: "Guard band",
                    3: "Stand Alone"
                }
            tmp = int(value, 16)
            Rast_OFFSET = hex2signedI16(value[4:])
            tmp = tmp >> 16
            Mode_OM = mapping.get(tmp & 0b11)
            data_dict["Rast_OFFSET"] = Rast_OFFSET
            data_dict["Mode_OM"] = Mode_OM
        elif key == "ECL":
            tmp = int(value, 16)
            ecl = tmp & 0b11
            tmp = tmp >> 2
            Trh_ECL1 = (tmp & 0xFF) - 140
            Trh_ECL2 = ((tmp >> 8) & 0xFF) - 140
            data_dict["ECL"] = ecl
            data_dict["Trh_ECL2"] = Trh_ECL2
            data_dict["Trh_ECL1"] = Trh_ECL1
        elif key == "TXP":
            nprach = hex2signedByte(value[6:])
            nprachmax = hex2signedByte(value[4:6])
            npusch = hex2signedByte(value[2:4])
            npuschmax = hex2signedByte(value[:2])
            # Store the split values in the dictionary
            data_dict["NPRACH"] = nprach
            data_dict["NPRACHMAX"] = nprachmax
            data_dict["NPUSCH"] = npusch
            data_dict["NPUSCHMAX"] = npuschmax
        elif key == "PLMN":
            value = revert_nibbles(value)
            value = value.replace("F"," ")
            value = value.lstrip('0')
            value 
            data_dict[key] = value
        elif key == "TAC":
            value = value[4:]
            data_dict[key] = value
        elif key == "EDRX":
            tmp = int(value, 16)
            drx = tmp & 0b11
            tmp = tmp >> 2
            edrx = ((tmp & 0x0F) - 1) * 20.48
            tmp = tmp >> 4
            ptwin = ((tmp & 0x0F) + 1) * 2.56
            data_dict["DRX"] = drx
            data_dict["EDRX"] = edrx
            data_dict["PTWIN"] = ptwin
        elif key == "PSM":
            tmp = int(value, 16)
            timerT3412 = tmp & 0xFF
            tmp = tmp >> 8
            timerT3412ext = tmp & 0xFF
            tmp = tmp >> 8
            timerT3324 = tmp & 0xFF
            data_dict["T3412"] = timerT3412
            data_dict["T3412ext"] = timerT3412ext
            data_dict["T3324"] = timerT3324
        elif key == "MIC":
            tmp = int(value, 16)
            RxLevMIN = (tmp & 0xFF) - 0x100
            tmp = tmp >> 8
            RxQualMIN = (tmp & 0xFF) - 0x100
            data_dict["RxLevMIN"] = RxLevMIN
            data_dict["RxQualMIN"] = RxQualMIN
        elif key == "EMM":
            tmp = int(value, 16)
            emm_mode = tmp & 0b1
            tmp = tmp >> 1
            emm_state = (tmp & 0b111)
            tmp = tmp >> 3
            emm_substate = (tmp & 0b1111)
            tmp = tmp >> 4
            rrc_state = (tmp & 0b1111)
            tmp = tmp >> 4
            rrc_substate = (tmp & 0b11111)
            tmp = tmp >> 5
            attach_flag = tmp & 0b1
            data_dict["emm_mode"] = emm_mode
            data_dict["emm_state"] = emm_state
            data_dict["emm_substate"] = emm_substate
            data_dict["rrc_state"] = rrc_state
            data_dict["rrc_substate"] = rrc_substate
            data_dict["attach_flag"] = attach_flag

        elif (key == "ENRG") | (key == "AEN") | (key == "SEN") :
            # Convert CID from hex to decimal
            value = str(int(value, 16))+"µWh"
            data_dict[key] = value
        
        #data_dict[key] = value

    # Print the separated data
    for key, value in data_dict.items():
        print(f"{key}: {value}",end=",")

    # Print all data, decoded or not
    # print("\nAll data, decoded or not:")
    # for pair in pairs:
    #     print(pair)

def AT_send_rcv(ser,cmd):
    send_at_command(ser, cmd)
    response = receive_response(ser, TR_WAIT)
    print_tsp(response)
    
def setup_lte_ltem(ser):
    lte_m_commands = [
    "AT+CFUN=0",
    "AT%XSYSTEMMODE=1,0,0,0",
    "AT+CGDCONT=0,\"IP\",\"test_ltem_dk\"",
    "AT+CFUN=1"
    ]
    for cmd in lte_m_commands:
        AT_send_rcv(ser, cmd)

def setup_lte_nbiot(ser):
    lte_nbiot_commands = [
    "AT+CFUN=0",
    "AT%XSYSTEMMODE=0,1,0,0",
    "AT+CGDCONT=0,\"IP\",\"test_nbiot_dk\"",
    "AT+CFUN=1"
    ]
    for cmd in lte_nbiot_commands:
        AT_send_rcv(ser, cmd)

def setup_lte_ltem_vodafone(ser):
    lte_ltem_commands = [
    "AT+CFUN=0",
    "AT%XSYSTEMMODE=1,0,0,0",
    "AT+CGDCONT=0,\"IP\",\"sensolus.iot\"",
    "AT+CFUN=1"
    ]
    for cmd in lte_ltem_commands:
        AT_send_rcv(ser, cmd)

def setup_lte_nbiot_vodafone(ser):
    lte_nbiot_commands = [
    "AT+CFUN=0",
    "AT%XSYSTEMMODE=0,1,0,0",
    "AT+CGDCONT=0,\"IP\",\"sensolus.iot\"",
    "AT+CFUN=1"
    ]
    for cmd in lte_nbiot_commands:
        AT_send_rcv(ser, cmd)

def wait_for_ok(ser, command, wait_time=TR_WAIT):
    """
    Send a command and wait for 'OK' in the response.
    """
    send_at_command(ser, command)
    response = ""
    timer_ok = timehr() + 1
    while (timehr() < timer_ok) and ("OK" not in response):
        response = receive_line(ser, wait_time)
        print_tsp(response)
    return response

def send_and_print(ser, command, wait_time=TR_WAIT):
    """
    Send a command, receive the response, and print it with timestamp.
    """
    send_at_command(ser, command)
    response = receive_response(ser, wait_time)
    print_tsp(response)
    return response

def socket_sequence(ser):
    """
    Perform the socket open, select, connect, send, and close sequence.
    """
    wait_for_ok(ser, "AT#XSOCKET=1,2,0,0")
    wait_for_ok(ser, "AT#XSOCKETSELECT=0")
    wait_for_ok(ser, "AT#XCONNECT=\"52.19.23.148\",6666")
    # Optionally enable RAI
    # wait_for_ok(ser, "AT#XSOCKETOPT=1,61,2")
    wait_for_ok(ser, "AT#XSEND=\"0123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789\"")
    wait_for_ok(ser, "AT#XSOCKET=0,2,0,0")  # socket closed

def monitor_sleep_loop(ser, loop_timeout):
    """
    Monitor for sleep and handle modem events.
    """
    timer1 = timehr() + TR_TIMEOUT
    while timehr() < timer1:
        response = receive_line(ser, TR_WAIT_LONG)
        if len(response) > 1:
            timer1 = timehr() + TR_TIMEOUT
        cleaned_text = re.sub(r"\s+", "", response)
        print_tsp(response)
        if "+CSCON:1" in cleaned_text:
            send_at_command(ser, "AT%XMONITOR")
        if "+CEREG" in cleaned_text:
            print_tsp("#RESEL OCCURED")
        if "SLEEP" in cleaned_text:
            break

def main():
    # Get the current date and time
    current_datetime = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"lognrf_{current_datetime}.txt"
    log_file = open(log_filename, "a")
    sys.stdout = DualOutput(sys.stdout, log_file)
    parser = argparse.ArgumentParser(description="A script that takes a command-line argument.")
    parser.add_argument('com', type=str, nargs='?', default="", help='comport of the modem')
    parser.add_argument("time", type=int, nargs='?', default=60, help="time interval")
    args = parser.parse_args()
    ser = serial.Serial()
    if len(args.com) < 3:
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(f"Device: {port.device}, Description: {port.description}, HWID: {port.hwid}")
        if len(ports) == 0:
            print("no ports found")
        exit()
    print(args.com, args.time, "\n")

    try:
        loop_timeout = args.time
        ser.port = args.com
        ser.baudrate = 115200
        ser.timeout = 1
        ser.open()

        send_and_print(ser, "AT")
        send_and_print(ser, "AT#SLEEPMODE=0")
        setup_lte_nbiot(ser)
        # setup_lte_ltem(ser)

        wait_for_ok(ser, "AT+CSCON=1")
        wait_for_ok(ser, "AT+XRAI=4")
        wait_for_ok(ser, "AT%XMODEMSLEEP=1,1000,60000")
        send_and_print(ser, "AT+CIMI")
        send_and_print(ser, "AT+COPS?")

        while True:
            send_and_print(ser, "AT")
            wait_for_ok(ser, "AT+CEREG?")
            send_and_print(ser, "AT%CONEVAL")
            socket_sequence(ser)
            monitor_sleep_loop(ser, loop_timeout)
            print_tsp(f"wait {loop_timeout}sec")
            if loop_timeout == 0:
                exit(0)
            sleep(loop_timeout)
    except KeyboardInterrupt:
        print("\nProgram interrupted. Closing the log file.")
    finally:
        log_file.close()
        print("Log file closed.")


if __name__ == "__main__":
    #sys.unraisablehook = custom_unraisablehook
    main()
    
