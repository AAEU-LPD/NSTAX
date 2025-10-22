import csv
import numpy as np
import pandas as pd
from io import StringIO
from datetime import datetime
import os
import csv
import matplotlib.pyplot as plt

class TrumiLogParserUtils:
    """Utility class for parsing TRUMI log files.
    """
    def __init__(self):
        self.test_cases = None
        self.test_folder = None

    def _clean_device_name(self, filename):
        name = os.path.splitext(filename)[0]
        name = name.replace("converted_", "").replace("_serial_data", "")
        return name

    def _find_test_folder(self, folder_name, base_path=""):
        if "results" in folder_name:
            return folder_name
        for dir in os.listdir(base_path):
            if folder_name.lower() in dir.lower() and os.path.isdir(os.path.join(base_path, dir)):
                return os.path.join(base_path, dir)
        raise FileNotFoundError(f"Test folder not found: {base_path}/{folder_name}")
        

    def _convert_csv_files(self, folder_path):
        for dir in os.listdir(folder_path):
            if not dir.startswith("converted") and dir.endswith(".csv"):
                csv_file_path = os.path.join(folder_path, dir)
                self.__convert_logs_raw(csv_file_path, folder_path + '/converted_' + dir)

    def _plot_converted_files(self, folder_path, testcase_label):
        data = []
        labels = []
        for dir in os.listdir(folder_path):
            if dir.startswith("converted") and dir.endswith(".csv"):
                converted_file_path = os.path.join(folder_path, dir)
                data.append(self.__read_csv(converted_file_path))
                labels.append('_'.join(dir.split('_')[1:]))
        self.__plot_multiple_data(data, labels, output_filepath=(folder_path + '/plot.png'), figure_title=testcase_label)
            
    def __convert_logs_raw(self, input_file_path, output_file_path):
        rawdata = self.__load_log(input_file_path)
        parsed_data = self.__parse_log(rawdata)
        parsed_data.to_csv(output_file_path, index=False)

    def __load_log(self, logFile):
        """Load the Trumi-related log data from a Lykaner or Skalli device."""
        try:
            with open(logFile, 'r',errors="ignore") as f:
                text = "\n".join([line for line in f if ((line.find("!") >= 0) and
                                (line.count(',') >= 9) and
                                (line.find('|<') < 0))])
            ds1 = pd.read_csv(StringIO(text), header=None, delimiter=',',
                            index_col=False, on_bad_lines='skip',
                            engine='c', low_memory=False)
        except: # noqa E722
            ds1 = pd.read_csv(logFile, header=None, delimiter=',',
                            index_col=False, on_bad_lines='skip',
                            engine='python')

        ds1.dropna(inplace=True)
        return ds1


    def __parse_log(self, ds1, time_column=0, start_time=None):
        """Parse the Trumi-related log data from a Lykaner or Skalli device."""
        def extract_time_string(s):
            return s[s.find('[')+1:s.find(']')]

        ret = pd.DataFrame()

        if time_column is not None:
            ret['Time'] = pd.to_datetime(
                ds1.loc[:, time_column].apply(extract_time_string))

        # Col 1: Device ID
        ret['DeviceID'] = ds1.loc[:, 1]

        # Col 2: Cycle index
        ret['Cycle'] = ds1.loc[:, 3].astype(str).apply(int, base=16)

        # Col 3: Accelerometer header (3 bytes)
        ret['acc_mode'] = ds1.loc[:, 3].astype(str).str[0:2].apply(int, base=16)
        ret['sample_index'] = ds1.loc[:, 3].astype(str).str[2:4].apply(int, base=16)
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
            
        # ret['Trumi_Event'] = ds1.loc[:, 16].astype(str).str[0:2].apply(int, base=16)
        # ret['Trumi_Rate'] = ds1.loc[:, 16].astype(str).str[2:].apply(int, base=16)
        # ret['Trumi_Event_Ext'] = ds1.loc[:, 17].astype(str)
        if len(ds1.columns) > 18:
            ret['trumi_state_ext'] = ds1.loc[:, 18].astype(str)
        
        # Create new trumi state column if 'trumi_state' is value 1 and 'trumi_state_ext' is value 1
        # Fix dtype warning by casting to float before assignment
        ret['trumi_state'] = ret['trumi_state'].astype(float)
        if 'trumi_state_ext' in ret.columns:
            ret.loc[(ret['trumi_state'] == 1) & (ret['trumi_state_ext'] == '1'), 'trumi_state'] = 1.5

        # ret.set_index('Time',inplace=True)
        if start_time is not None:
            ret['Time'] += (start_time-ret['Time'][0])

        ret.index = ret['Time']
        return ret     
    
    # PLOTTING FUNCTIONS
    def __read_csv(self, filepath):
        data = []
        with open(filepath, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                timestamp = datetime.strptime(row['Time'], '%Y-%m-%d %H:%M:%S.%f')
                trumi_state = float(row['trumi_state'])
                vel = float(row['Vel'])
                dist = float(row['Dist'])
                acc_x = float(row['Acc_x'])
                acc_y = float(row['Acc_y'])
                acc_z = float(row['Acc_z'])
                data.append((timestamp, trumi_state, vel, dist, acc_x, acc_y, acc_z))
        return data

    def __plot_multiple_data(self, data_sets, labels, output_filepath, figure_title='Figure', show_plot=False):
        plt.figure(figsize=(14, 12))
        plt.suptitle(figure_title)

        for i, data in enumerate(data_sets):
            timestamps = [entry[0] for entry in data]
            trumi_states = [entry[1] for entry in data]
            velocities = [entry[2] for entry in data]
            distances = [entry[3] for entry in data]
            accel_x = [entry[4] for entry in data]
            accel_y = [entry[5] for entry in data]
            accel_z = [entry[6] for entry in data]

            plt.subplot(3, 2, 1)
            plt.plot(timestamps, trumi_states, label=f'Trumi State ({labels[i]})')
            plt.xlabel('Timestamp')
            plt.ylabel('Trumi State')
            plt.title('Time vs Trumi State')
            plt.legend()

            plt.subplot(3, 2, 3)
            plt.plot(timestamps, velocities, label=f'Velocity ({labels[i]})')
            plt.xlabel('Timestamp')
            plt.ylabel('Velocity')
            plt.title('Time vs Velocity')
            plt.legend()

            plt.subplot(3, 2, 5)
            plt.plot(timestamps, distances, label=f'Distance ({labels[i]})')
            plt.xlabel('Timestamp')
            plt.ylabel('Distance')
            plt.title('Time vs Distance')
            plt.legend()

            plt.subplot(3, 2, 2)
            plt.plot(timestamps, accel_x, label=f'Accel X ({labels[i]})')
            plt.xlabel('Timestamp')
            plt.ylabel('Accel X')
            plt.title('Time vs Accel X')
            plt.legend()

            plt.subplot(3, 2, 4)
            plt.plot(timestamps, accel_y, label=f'Accel Y ({labels[i]})')
            plt.xlabel('Timestamp')
            plt.ylabel('Accel Y')
            plt.title('Time vs Accel Y')
            plt.legend()

            plt.subplot(3, 2, 6)
            plt.plot(timestamps, accel_z, label=f'Accel Z ({labels[i]})')
            plt.xlabel('Timestamp')
            plt.ylabel('Accel Z')
            plt.title('Time vs Accel Z')
            plt.legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(output_filepath)
        if show_plot:
            plt.show()
            
class TrumiStateAnalysis(TrumiLogParserUtils):
    """Class for analyzing TRUMI state transition logs.
    """
    def __init__(self, results_folder):
        super().__init__()
        self.test_cases = [
             'datalogs_TRUMI_State_Transition_TRUMI',
             'datalogs_TRUMI_State_Transition_RELOC',
             'datalogs_TRUMI_State_Transition_Keep_TRUMI_Variables',
             'datalogs_TRUMI_State_Transition_Clear_TRUMI_Variables', 
            ]
        self.descriptions = {
            'datalogs_TRUMI_State_Transition_TRUMI': "Test for TRUMI state transitions: verifies correct state changes between SLEEP, TRUMI, and LIGHT_SLEEP.",
            'datalogs_TRUMI_State_Transition_RELOC': "Test for RELOC state transitions: checks transitions through SLEEP, TRUMI, and RELOC states.",
            'datalogs_TRUMI_State_Transition_Keep_TRUMI_Variables': "Test for state transitions with TRUMI variables retained: ensures state and variable persistence across transitions.",
            'datalogs_TRUMI_State_Transition_Clear_TRUMI_Variables': "Test for state transitions with TRUMI variables cleared: validates correct state changes and variable resets."
        }
        # Mapping of test case names to their expected trumi_state transitions
        self.expected_transitions = {
            'datalogs_TRUMI_State_Transition_TRUMI': [1.0, 2.0, 1.0, 1.5, 1.0],
            'datalogs_TRUMI_State_Transition_RELOC': [1.0, 2.0, 3.0, 1.0],
            'datalogs_TRUMI_State_Transition_Keep_TRUMI_Variables': [1.0, 2.0, 1.0, 1.5, 2.0, 3.0, 1.0],
            'datalogs_TRUMI_State_Transition_Clear_TRUMI_Variables': [1.0, 2.0, 1.0, 1.5, 1.0, 2.0, 3.0, 1.0],
        }
        self.test_folder = results_folder
        self.transition_type = type('TransitionType', (), {})  # Create a simple class for transition types
        self.test_instances = []
    
    def start_analysis(self):
        test_folder = self._find_test_folder(self.test_folder)
        for testcase in self.test_cases:
            folder_path = os.path.join(test_folder, testcase)
            if not os.path.exists(folder_path):
                print(f"Folder does not exist: {folder_path}. Skipping testcase {testcase}.")
                continue
            self._convert_csv_files(folder_path)
            self._plot_converted_files(folder_path, testcase_label=testcase)
            plot_html = f'''<img class="result-output" src="{os.path.join(testcase, "plot.png")}">'''
            state_transitions, device_names = self.check_transitions(folder_path)
            expected = self.expected_transitions.get(testcase, [])
            verdicts = []
            actual_transitions = []
            if expected:
                for idx_arr, states in enumerate(state_transitions):
                    min_len = min(len(expected), len(states))
                    mismatches = []
                    for i in range(min_len - 1):
                        expected_pair = (expected[i], expected[i + 1])
                        actual_pair = (states[i], states[i + 1])
                        if expected_pair != actual_pair:
                            mismatches.append((i, expected_pair, actual_pair))
                    if len(expected) != len(states):
                        mismatches.append(("length_mismatch", None, None))
                    verdict = "PASSED" if not mismatches else "FAILED"
                    verdicts.append(verdict)
                    actual_transitions.append(states)
            print(f"Expected Transitions: {expected}")
            for idx, states in enumerate(actual_transitions):
                print(f"Device {idx+1}: {states} Verdict: {verdicts[idx]}")
            # For each expected state, create a step with the description "Checking for the TRUMI(<state>) state"
            result_step = {}
            for idx, (states, verdict, device_name) in enumerate(zip(actual_transitions, verdicts, device_names), start=1):
                result_step[str(idx)] = {
                    "step_description": f"Checking state transition for \"{device_name}\"",
                    "expected_result": f"Expected: {expected}",
                    "actual_result": f"Actual: {states}",
                    "verdict": verdict
                }
            final_verdict = "PASSED" if all(v == "PASSED" for v in verdicts) else "FAILED"
            test_instance = TestCaseResult(
                description=self.descriptions.get(testcase, testcase),
                name=testcase,
                version=0.1,
                dut_info=None,
                result_output={"table": None, "image": plot_html},
                result=final_verdict,
                result_step=result_step
            )
            self.test_instances.append(test_instance)

    def check_transitions(self, folder_path):
        converted_files = [f for f in os.listdir(folder_path) if f.startswith('converted') and f.endswith('.csv')]
        if len(converted_files) < 2:
            raise ValueError("Not enough converted files found in the directory.")
        data_path_1 = os.path.join(folder_path, converted_files[0])
        data_path_2 = os.path.join(folder_path, converted_files[1])
        device1 = self._clean_device_name(converted_files[0])
        device2 = self._clean_device_name(converted_files[1])
        df1 = pd.read_csv(data_path_1, parse_dates=['Time'])
        df2 = pd.read_csv(data_path_2, parse_dates=['Time'])
        states1 = self.__calculate_state_transitions(df1)
        states2 = self.__calculate_state_transitions(df2)
        state_transitions = [states1, states2]
        device_names = [device1, device2]
        return state_transitions, device_names

    def __calculate_state_transitions(self, df1):
        # Collapse consecutive rows with the same trumi_state into intervals with start and end times
        collapsed = []
        prev_state = None
        for idx, row in df1.iterrows():
            curr_state = row['trumi_state']
            if prev_state is None:
                prev_state = curr_state
            elif curr_state != prev_state:
                collapsed.append({
                    'trumi_state': prev_state
                })
            prev_state = curr_state
        # Add the last interval
        if prev_state is not None:
            collapsed.append({
            'trumi_state': prev_state
            })
        # Build an array of consecutive trumi_state values (no repeats)
        consecutive_states = []
        for interval in collapsed:
            state = interval['trumi_state']
            if not consecutive_states or consecutive_states[-1] != state:
                consecutive_states.append(state)
        return consecutive_states

class TestCaseResult:
    def __init__(self, description, name, dut_info, result_output, version, result, result_step):
        self.description = description
        self.name = name
        self.version = version
        self.dut_info = dut_info
        self.result_output = result_output
        self.result = result
        self.result_step = result_step

class AnalysisResult:
    def __init__(self, name, test_instances):
        self.name = name
        self.test_instances = test_instances

class TrumiBenchmarkAnalysis(TrumiLogParserUtils):
    """Class for analyzing TRUMI benchmark logs.
    """
    def __init__(self, results_folder):
        super().__init__()
        self.test_cases = ['datalogs_TRUMI_Benchmark',]
        self.test_folder = results_folder
        self.test_instances = []
        
    def start_analysis(self):
        test_folder = self._find_test_folder(self.test_folder)
        for testcase in self.test_cases:
            folder_path = os.path.join(test_folder, testcase)
            if not os.path.exists(folder_path):
                print(f"Folder does not exist: {folder_path}. Skipping testcase {testcase}.")
                continue
            self._convert_csv_files(folder_path)
            self._plot_converted_files(folder_path, testcase_label=testcase)
            self.calculate_trumi_statistics(folder_path, testcase)

    def calculate_trumi_statistics(self, folder_path, testcase):
        converted_files = [f for f in os.listdir(folder_path) if f.startswith('converted') and f.endswith('.csv')]
        # Use the converted file names from the directory listing
        if len(converted_files) < 2:
            raise ValueError("Not enough converted files found in the directory.")
        data_path_1 = os.path.join(folder_path, converted_files[0])
        data_path_2 = os.path.join(folder_path, converted_files[1])
        # Extract device names from the converted file names (without extension)
        device1 = self._clean_device_name(converted_files[0])
        device2 = self._clean_device_name(converted_files[1])
        df1 = pd.read_csv(data_path_1, parse_dates=['Time'])
        df2 = pd.read_csv(data_path_2, parse_dates=['Time'])
        row1 = self.__process_data(df1, device1)
        row2 = self.__process_data(df2, device2)
        # Calculate the difference row (row2 - row1 for numeric columns)
        diff_row = [f"Difference in variables", ""]  # Device and Duration columns
        for v1, v2 in zip(row1[2:], row2[2:]):
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                diff = v2 - v1
            else:
                try:
                    diff = float(v2) - float(v1)
                except Exception:
                    diff = ""
            diff_row.append(diff)
        summary_filename = f"{folder_path}/summary_{self.test_folder}.csv"
        # Write CSV summary
        with open(summary_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
            "Device", "Duration", "Time_in_trumi", "Time_in_reloc", "Time_in_sleep", "Num_Of_Trumi", "Num_Of_Reloc", "False_Triggers", "Reloc_Transitions", "Trumi_Transitions"
            ])
            writer.writerow(row1)
            writer.writerow(row2)
            writer.writerow(diff_row)


        # Prepare HTML summary and store as class variable
        # Only include all columns except the last two (i.e., exclude reloc_transitions and trumi_transitions)
        headers = [
            "Device", "Duration", "Time_in_trumi", "Time_in_reloc", "Time_in_sleep", "Num_Of_Trumi", "Num_Of_Reloc", "False_Triggers"
        ]
        # Remove last two columns from each row
        rows = [row1[:-2], row2[:-2], diff_row[:-2]]
        html_table = "<table class=\"result-output\" border='1'>\n<tr>{}</tr>\n".format(''.join(f"<th>{h}</th>" for h in headers))
        for row in rows:
            html_table += "<tr>{}</tr>\n".format(''.join(f"<td>{str(cell).replace(chr(10), '<br>')}</td>" for cell in row))
        html_table += "</table>\n"
        plot_html = f'''<img class="result-output" src="{os.path.join(testcase, "plot.png")}">'''
        # For each expected state, create a step with the description "Checking for the TRUMI(<state>) state"
        result_step = {}
        result_step[1] = {
            "step_description": f"Calculating benchmarks, generating statistics\"",
            "expected_result": f"-",
            "actual_result": f"-",
            "verdict": "PASSED"
        }
        test_instance = TestCaseResult(
            description=testcase,
            name=testcase,
            version=0.1,
            dut_info=None,
            result_output={"table": html_table, "image": plot_html},
            result="PASSED",
            result_step=result_step
        )
        self.test_instances.append(test_instance)

    def __process_data(self, df, device):
        duration = df['Time'].iloc[-1] - df['Time'].iloc[0]
        time_in_trumi = round(df[df['trumi_state'] == 2]['Time'].diff().sum().total_seconds())
        time_in_reloc = round(df[df['trumi_state'] == 3]['Time'].diff().sum().total_seconds())
        time_in_sleep = round(df[df['trumi_state'].isin([1, 1.5])]['Time'].diff().sum().total_seconds())

        transitions = []
        for i in range(1, len(df)):
            prev = df.iloc[i-1]['trumi_state']
            curr = df.iloc[i]['trumi_state']
            prev_state = (
                "SLEEP" if prev == 1 else
                "RELOC" if prev == 3 else
                "TRUMI" if prev == 2 else
                "LIGHT_SLEEP" if prev == 1.5 else
                str(prev)
            )
            curr_state = (
                "SLEEP" if curr == 1 else
                "RELOC" if curr == 3 else
                "TRUMI" if curr == 2 else
                "LIGHT_SLEEP" if curr == 1.5 else
                str(curr)
            )
            if (
                (prev == 1 and curr == 2) or
                (prev == 2 and curr == 1) or
                (prev == 1 and curr == 2) or
                (prev == 1.5 and curr == 2) or
                (prev == 1.5 and curr == 1) or
                (prev == 2 and curr == 3) or
                (prev == 3 and curr == 1)
            ):
                transitions.append(f"{prev_state} {curr_state} {df.iloc[i]['Time']}")    
        num_of_trumi = sum(
            1 for i in range(1, len(df))
            if (
                (df.iloc[i-1]['trumi_state'] == 1 and df.iloc[i]['trumi_state'] == 2)
            )
        )
        num_of_reloc = sum(
            1 for i in range(1, len(df))
            if (
                (df.iloc[i-1]['trumi_state'] == 2 and df.iloc[i]['trumi_state'] == 3)
            )
        )
        false_triggers = round((num_of_trumi - num_of_reloc) / num_of_trumi * 100, 2)
        # Find all transitions from TRUMI to RELOC and join them with newlines
        reloc_transitions = "\n".join(
            f"TRUMI RELOC {df.iloc[i]['Time']}"
            for i in range(1, len(df))
            if df.iloc[i-1]['trumi_state'] == 2 and df.iloc[i]['trumi_state'] == 3
        )
        trumi_transitions = "\n".join(
            f"SLEEP TRUMI {df.iloc[i]['Time']}"
            for i in range(1, len(df))
            if df.iloc[i-1]['trumi_state'] == 1 and df.iloc[i]['trumi_state'] == 2
        )
        # Assign to row
        row = [
            device,
            str(duration),
            time_in_trumi,
            time_in_reloc,
            time_in_sleep,
            num_of_trumi,
            num_of_reloc,
            false_triggers,
            reloc_transitions,  # Add the reloc transitions as a new row element
            trumi_transitions,  # Add the trumi transitions as a new row element
        ]
        return row
        
    def __load_autolog(self, test_folder_name, folder_path): 
        folder_path = f'{folder_path}/{test_folder_name}'
        autolog_path = os.path.join(folder_path, 'autolog.txt')
        if not os.path.exists(autolog_path):
            raise FileNotFoundError(f"autolog.txt not found in {folder_path}")
        with open(autolog_path, 'r') as f:
            lines = f.readlines()
        shake_times = []
        for line in lines:
            # Example line: "[2024-07-16 15:20:38.123] Start Shaking at 5Hz 0.2Vpp for 1800 seconds"
            if "Start Shaking at" in line:
                ts = line.split('|NSTA')[0].strip()
                # Extract frequency, voltage, and duration using split
                parts = line.split("Start Shaking at")[1].strip().split()
                freq = parts[0]  # e.g., '5Hz'
                voltage = parts[1]  # e.g., '0.2Vpp'
                duration = parts[3]  # e.g., '1800'
                shake_times.append((ts, "Start Shaking", freq, duration, voltage))
            elif "Stop Shaking" in line:
                ts = line.split('|NSTA')[0].strip()
                shake_times.append((ts, "Stop Shaking", freq, duration, voltage))
                
        # Write shake events to CSV
        shake_events_filename = f"shake_events_{test_folder_name}.csv"
        with open(shake_events_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Event Type", "Frequency", "Duration", "Voltage"])
            # Write Shake Started events with freq, duration, voltage
            for ts, event_type, freq, duration, voltage in shake_times:
                writer.writerow([ts, event_type, freq, duration, voltage])
        
class trumi_log_parser:
    def __init__(self, results_folder, analysis_type):
        self.results_folder = results_folder
        self.analysis_type = analysis_type
        # State types
        self.state_type = type('StateType', (), {})  # Create a simple class for state types
        self.state_type.STATE_ONLY = 1
        self.state_type.BENCHMARK_ONLY = 2
        self.state_type.FULL_ANALYSIS = 3
        self.test_instances = []

    def run_script(self):
        if self.analysis_type == self.state_type.STATE_ONLY:
            state_analysis = TrumiStateAnalysis(self.results_folder)
            state_analysis.start_analysis()
            self.test_instances = state_analysis.test_instances
        elif self.analysis_type == self.state_type.BENCHMARK_ONLY:
            benchmark_analysis = TrumiBenchmarkAnalysis(self.results_folder)
            benchmark_analysis.start_analysis()
            self.test_instances = benchmark_analysis.test_instances
        elif self.analysis_type == self.state_type.FULL_ANALYSIS:
            state_analysis = TrumiStateAnalysis(self.results_folder)
            benchmark_analysis = TrumiBenchmarkAnalysis(self.results_folder)
            state_analysis.start_analysis()
            benchmark_analysis.start_analysis()
            self.test_instances = state_analysis.test_instances + benchmark_analysis.test_instances

    def get_result_suite(self):
        # Example usage:
        analysis_result = AnalysisResult(
            name="Trumi_Log_Analysis_Script_Results",
            test_instances=self.test_instances
        )
        return analysis_result


if __name__ == "__main__":
    TEST_FOLDER_NAME = "test_20250730_145107"
    TEST_CASES = ['datalogs_TRUMI_Benchmark',
             'datalogs_TRUMI_State_Transition_TRUMI',
             'datalogs_TRUMI_State_Transition_RELOC',
             'datalogs_TRUMI_State_Transition_Clear_TRUMI_Variables', 
             'datalogs_TRUMI_State_Transition_Keep_TRUMI_Variables',
            ]
    parser = TrumiLogParserUtils()
    test_folder = parser.find_test_folder(TEST_FOLDER_NAME)
    for testcase in TEST_CASES:
        folder_path = os.path.join(test_folder, testcase)
        parser.convert_csv_files(folder_path)
        parser.plot_converted_files(folder_path, testcase_label=testcase)
