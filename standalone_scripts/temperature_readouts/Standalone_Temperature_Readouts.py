"""Read Temperature Data form Platform Devices (Tested on HATI).

This standalone script:
    1. Crawls through all Keepalive messages of a device within given timeframe
    2. Captures message generation timestamp and temperature data, saves in python structure for further use
    3. Optionally, generates a csv file out of it

Makes use of the following features of the NSTA framework:
    1. PlatformDevice: To get device specific messages
"""


import csv
from NSTA.devices.platform_device import PlatformDevice


def get_device_messages(device_id, start_time_utc, end_time_utc, max_n_messages):
    """Get raw FW maeesages with given conditions.

        :param device_id: Target Platform Device ID
        :type device_id: int
        :param start_time_utc: Returns messages only from this ISO 8601 UTC timestamp onwards, defaults to a day before current UTC time
        :type start_time_utc: str
        :param end_time_utc: Returns messages upto this ISO 8601 UTC timestamp, defaults to current UTC timestamp captured from the system
        :type end_time_utc: str
        :param max_n_messages: Max. number of messages returned, defaults to 50
        :type max_n_messages: int

        :return: List of messages
        :rtype: list
    """
    backend_messages = []
    # Create device instance
    device_instance = PlatformDevice("MyHatiDevice", device_id)
    # Connect to the device instance
    device_instance.connect()
    # Get backend messages
    backend_messages = device_instance.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_messages=max_n_messages)
    # Reverse message list (earlier first)
    backend_messages = list(reversed(backend_messages))
    return backend_messages

def get_temperature(device_messages):
    """Capture Timestamp and Temperature Data.
        :param device_messages: List of raw device messages
        :type device_messages: list

        :return: List of timestamp and temperature data
        :rtype: list
    """
    temperature_list = []
    snapshot_template = {
        "timestamp": "",
        "temperature": -999
    }
    # Crawl through messages
    for message in device_messages:
        try:
            timestamp = message["decodedMsg"]["messageDate"]
            temperature = message["decodedMsg"]["keepAliveMetricValues"]["TEMPERATURE"]
            snapshot = snapshot_template.copy()
            snapshot["timestamp"] = timestamp
            snapshot["temperature"] = temperature
            temperature_list.append(snapshot)
        except KeyError as e_:
            # Message does not contain timestamp / temperature, skip
            pass
    return temperature_list

def write_csv(filename, temperature_list):
    """Write Date to CSV File.
        :param filename: Filename with absoute path
        :type filename: str
    """
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp[YYYY-MM:DDTHH:MM:SS+0000]", "temperature[C]"])
        for snapshot in temperature_list:
            writer.writerow([snapshot["timestamp"], snapshot["temperature"]])


if __name__ == "__main__":
    # Main Function, User inputs are to be updated only here
    # ORG_ID = 3861         # Alps N5 dev Team
    ORG_ID = 4604           # HATI dev
    DEVICE_ID = 511934      # XULUZ2
    MAX_N_MESSAGES = 50
    START_TIME_UTC = "2024-05-07T00:00:00"
    END_TIME_UTC = "2024-05-08T00:00:00"

    WRITE_CSV = False
    CSV_REPORT_FILENAME = "C:/UserData/dev/NSTA/standalone_scripts/temperature_readouts/result.csv"

    device_messages = get_device_messages(DEVICE_ID, START_TIME_UTC, END_TIME_UTC, MAX_N_MESSAGES)
    temperature_list = get_temperature(device_messages)

    if WRITE_CSV:
        # Write in CSV file
        write_csv(CSV_REPORT_FILENAME, temperature_list)
    else:
        # Print (pretty) in console
        from pprint import pprint
        pprint(temperature_list)
