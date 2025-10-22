from pathlib import Path
from argparse import ArgumentParser
import numpy as np
import pandas as pd
from io import StringIO
from datetime import datetime

# def parse_measurement(self, filename="", suffix=""):
#     if self.dev_name == "N5" or self.dev_name == "L5":
#         CL = ConvertLogs()
#         filename = f'{filename}{self.dev_name}_parsed_data{suffix}.csv'
#         CL.convert(self.data_filename, filename)
#         os.remove(self.data_filename)
#     elif self.dev_name == "HATI":
#         filename = f'{filename}{self.dev_name}_parsed_data{suffix}.csv'
#         os.rename(self.data_filename,filename)

class ParsingUtils():
    def __init__(self):
        pass

    def load_log(self, logFile):
        """Load the Trumi-related log data from a Lykaner or Skalli device."""
        try:
            ds1 = pd.read_csv(logFile, header=None, delimiter=',',
                              index_col=False, on_bad_lines='skip',
                              engine='python')
        except pd.errors.EmptyDataError:  # noqa E722
            ds1 = pd.DataFrame()

        ds1.dropna(inplace=True)
        return ds1

    def parse_log(self, ds1, time_column=0, start_time=None):
        """Parse the Trumi-related log data from a Lykaner or Skalli device."""
        
        def extract_time_string(s):
            return s[s.find('[')+1:s.find(']')]

        ret = pd.DataFrame()
        
        if ds1.empty:
            return ret

        if time_column is not None:
            ret['Time'] = pd.to_datetime(
                ds1.loc[:, time_column].apply(extract_time_string))

        # Col 1: Device ID
        ret['DeviceID'] = ds1.loc[:, 1]

        # Col 2: Cycle index
        ret['Cycle'] = ds1.loc[:, 3].astype(str).apply(int, base=16)

        # Col 3: Accelerometer header (3 bytes)
        ret['acc_mode'] = ds1.loc[:, 3].astype(str).str[0:2].apply(int, base=16)
        ret['sample_index'] = ds1.loc[:, 3].astype(
            str).str[2:4].apply(int, base=16)
        ret['trumi_state'] = ds1.loc[:, 3].astype(str).str[4:].apply(int, base=16)

        # Col 4: RTC
        ret['RTC_stamp'] = ds1.loc[:, 4].apply(int, base=16)
        ret['RTC_time'] = ret.loc[:, 'RTC_stamp'].apply(datetime.fromtimestamp)

        if time_column is None:
            ret['Time'] = ret['RTC_time']

        #  Col 5: Speed
        ret['Vel'] = ds1.loc[:, 5].astype(int)

        # Col 6: Distance
        ret['Dist'] = ds1.loc[:, 6].astype(int)

        # Col 7-9: Acceleration
        ret['Acc_x'] = ds1.loc[:, 7].astype(int)
        ret['Acc_y'] = ds1.loc[:, 8].astype(int)
        ret['Acc_z'] = ds1.loc[:, 9].astype(int)
        ret['Acc_abs'] = np.linalg.norm(ret[['Acc_x', 'Acc_y', 'Acc_z']], axis=1)

        # Extended output
        if len(ds1.columns) > 10:
            # Additionally in the extended log(you have extended one)
            # there are gravity(xyz) vector and direction vector(xyz)
            # at the end "-54,-982,14,0,0,0"
            ret['Grav_x'] = ds1.loc[:, 10].astype(int)
            ret['Grav_y'] = ds1.loc[:, 11].astype(int)
            ret['Grav_z'] = ds1.loc[:, 12].astype(int)
            ret['Grav_abs'] = np.linalg.norm(
                ret[['Grav_x', 'Grav_y', 'Grav_z']], axis=1)

            ret['Dir_x'] = ds1.loc[:, 13].astype(int)
            ret['Dir_y'] = ds1.loc[:, 14].astype(int)
            ret['Dir_z'] = ds1.loc[:, 15].astype(int)
            ret['Dir_abs'] = np.linalg.norm(
                ret[['Dir_x', 'Dir_y', 'Dir_z']], axis=1)

            ret['Dir_norm_x'] = ret['Dir_x']/ret['Dir_abs']
            ret['Dir_norm_y'] = ret['Dir_y']/ret['Dir_abs']
            ret['Dir_norm_z'] = ret['Dir_z']/ret['Dir_abs']

        # ret.set_index('Time',inplace=True)
        if start_time is not None:
            ret['Time'] += (start_time-ret['Time'][0])

        ret.index = ret['Time']
        return ret

    def parseGPSNmea(self, gpsfile, date=None):
        """ Parse velocity, location and heading direction from a file
        in NMEA format"""
        with open(gpsfile) as f:
            text = "\n".join([line for line in f if (line.startswith('$GPRMC'))])

        ds_gps = pd.read_csv(StringIO(text), sep=',', error_bad_lines=False,
                             keep_default_na=False,  skiprows=0, header=None)

        # Skip invalid data
        idx_ok = np.logical_and(
            (ds_gps.loc[:, 2] == 'A'),  (ds_gps.loc[:, 12].str[0] == 'A'))
        ds_gps = ds_gps.loc[idx_ok, :]
        ds_gps.reset_index(inplace=True, drop=True)

        format_str = "%H%M%S.%f"

        # Date on the GPS device is wrong...
        # date_str = "%d%m%Y"

        ds_parsed = pd.DataFrame()

        ds_parsed['Time'] = pd.to_datetime(
            ds_gps[1].astype(str), format=format_str)
        ds_parsed['Latitude'] = ds_gps[3]
        ds_parsed['Longitude'] = ds_gps[5]
        ds_parsed['Speed'] = ds_gps[7].astype(float)*float(1.8)
        ds_parsed['Heading'] = ds_gps[8]

        if date is not None:
            ds_parsed['Time'] = ds_parsed['Time'].apply(
                lambda x: (x.replace(year=date.year,
                                     month=date.month,
                                     day=date.day)))

        ds_parsed.index = ds_parsed.Time

        return ds_parsed

    def load_processed(self, path):
        """Load a devoce log file converted to tabular form"""
        ds_parsed = pd.read_csv(path, parse_dates=['Time'])
        ds_parsed.index = ds_parsed['Time']
        return ds_parsed


class ConvertAccelLogs():
    def __init__(self):
        pass

    def convert(self, input_file_path, output_file_path):
        PU = ParsingUtils()
        rawdata = PU.load_log(input_file_path)
        parsed_data = PU.parse_log(rawdata)
        parsed_data.to_csv(output_file_path, index=False)