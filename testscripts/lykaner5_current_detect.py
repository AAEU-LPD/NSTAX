"""Current State Detection logic for Lykaner5 platform devices

This module is to be used for current state detection from a measured current graph.
"""

import pandas as pd
import numpy as np

#########################################################################
###          State classes to represent each current state            ###
#########################################################################
from enum import Enum

class StateName(Enum):
    """
    Labels for different state types
    """
    LED_5 = 1
    LED_10 = 2
    UL_ACT = 3
    UL_DLRQ = 4
    UL_KA = 5
    UL_MAC = 6
    DL_ACK = 7
    WIFI_SCAN = 8
    WIFI_SCAN_2 = 9
    UNKNOWN = 10
    
class ReferenceState:
    """
    Represents a current reference state (for eg: LED, UL_DL, WiFi)
    
    :param file: file name of reference grpah
    :type file: str
    :param name: name of the reference state
    :type name: str
    """
    def __init__(self, file, name):
        self.name = name
        
        # Extract data into two arrays
        df =  pd.read_csv(file)
        self.ref_curr = df['Current'].values
        self.ref_time = df['Time'].values


#########################################################################
###                       Current Detection Logic                     ###
#########################################################################
class CurrentDetector:
    """ Represents the current detection utility functions.
    
    Features including: loading reference states, formatting measurement data
                        calculating averages, calling detection logic for computation

    :param detect_state_name: name of the state to evaluate
    :type detect_state_name: str
    :param data_filename: name of the current measurement file
    :type data_filename: str
    :param data_folder: location of the current measurement file, defaults to "static/current_measurement/"
    :type data_folder: str, optional
    :param ref_folder: location of the reference graph files, defaults to "ref_current_graphs/"
    :type ref_folder: str, optional
    """
    def __init__(self, detect_state_name, data_filename, data_folder="static/current_measurement/", ref_folder="static/ref_current_graphs/"):
        ### Main data file to assess
        data_filename = data_folder + data_filename
        self.data = pd.read_csv(f'{data_filename}')
        
        ### LOADING THE REFERENCE STATES
        try:
            #[TODO]: modify this to only load the state based on string name instead of all
            self.ref_states_list = [
                ReferenceState(ref_folder + 'ref_act_ifft_led5.csv', StateName.LED_5), 
                ReferenceState(ref_folder + 'ref_act_ifft_led10.csv', StateName.LED_10), 
                ReferenceState(ref_folder + 'ref_act_ifft_wifi.csv', StateName.WIFI_SCAN), 
                ReferenceState(ref_folder + 'ref_act_ifft_ul3.csv', StateName.UL_ACT), 
                ReferenceState(ref_folder + 'ref_act_ifft_ul12.csv', StateName.UL_MAC), #act2 fail
                ReferenceState(ref_folder + 'ref_act_ifft_rx.csv', StateName.UL_DLRQ), 
            ]
        except FileNotFoundError:
            print("File not found. Unable to load data.")
            return 
        
        # Find the matching reference and set interval count -> resolution for matching filter comparison
        for state in self.ref_states_list:
            if state.name.name == detect_state_name:
                self.reference_state = state
                
        if self.reference_state.name == StateName.LED_10:
            self.interval_count = 0.25
        elif self.reference_state.name == StateName.UL_ACT:
            self.interval_count = 0.25
        elif self.reference_state.name == StateName.UL_MAC:
            self.interval_count = 0.20
        elif self.reference_state.name == StateName.UL_DLRQ:
            self.interval_count = 1.0
        else: 
            self.interval_count = 0.5
            
        # Indicators   
        self.is_eof = False
                
    def _format_data(self): 
        """ Adjust the measurement values to a usable format
        """
        # Conversion of units for PPK generated values
        self.data['Current'] = self.data['Current'].div(1000000) #from uA to A
        self.data['Time'] = self.data['Time'] - self.data['Time'][0] #Remove offset
        self.data['Time'] = self.data['Time'].div(1000) # from ms to s
            
        # Setup data for for calculations
        self.orig_data = self.data
        self.data = self.data.reset_index(drop=True)
        
        # Extract the 'Time' and 'Current' columns
        self.time = self.data['Time']
        self.current = self.data['Current'] # Used for moving average calculation
        self.orig_current = self.orig_data['Current'] 
        
        # Round to 3 decimal places
        time_round_val = 1000.0
        self.time = self.time.mul(time_round_val)
        self.time = np.floor(self.time)
        self.time = self.time.div(time_round_val)
        
        # Adjust offset in reference graph
        average_cycle_current_ref = 12.7468 # (mA) Based on the training graph [avg_curr of entire activation cycle]
        average_cycle_current_orig = self.current.mean()*1000
        
        current_offset = (average_cycle_current_orig - average_cycle_current_ref)/1000    
        
        self.reference_state.ref_curr += current_offset
        
    def _calculate_moving_average(self):
        """ Calculate the moving average of the current measurement to get a smoother graph
        """
        mva_window = 100
        
        # Calculate the moving average
        self.window_size = int(mva_window)  # Adjust the window size as needed
        self.moving_average = self.current.rolling(window=self.window_size).mean().fillna(0)       
        
    def _compute_decision_logic(self): 
        """ Call the CurrentLogic() class for computation of the decision logic to detect the state
        """
        current_logic = CurrentLogic(self.time, self.orig_current, self.moving_average, self.reference_state)       
        # Loop till end of file
        while not self.is_eof:
            self.is_eof = current_logic.correlate_signal(self.interval_count)
            
        self.state_table = current_logic.get_output_table()
        
    def _save_output(self):
        """ Save the detected states to a .csv file
        """
        # Save the updated DataFrame to the CSV file
        self.state_table.to_csv('state_table.csv', index=False)
        
    def run_current_detector(self):
        """ Execute each step required for the current state detection
        """
        print("[LOG] CurrentDetector: Formatting data...")
        self._format_data()
        print("[LOG] CurrentDetector: Calculating moving average...")
        self._calculate_moving_average()
        print("[LOG] CurrentDetector: Detecting states...")
        self._compute_decision_logic()
        print("[LOG] CurrentDetector: Saving output...")
        self._save_output()
        
    def get_states(self):
        """ Return the detected and stored states
        
        :return: detected states from the stored csv
        :rtype: pandas.DataFrame()
        """
        output =  pd.read_csv('state_table.csv')
        os.remove('state_table.csv')
        
        return output                    
    

from scipy.signal import argrelextrema

class CurrentLogic:
    """Holds the logic and decision making for CurrentDetector class

    Compares the reference state window across the measured current graph.
    Correlation and other parameters are evaluated between the reference and orignal
    signal. Parameters are used to evaluate whether the selected section is similar
    to the reference state.


    :param time: time column values of the original measurement
    :type time: Series()
    :param current: current column values of the original measurement
    :type current: Series()
    :param mva: moving average of the current values
    :type mva: pandas.DataFrame()()
    :param ref_state: state to detect
    :type ref_state: ReferenceState()
    """
    def __init__(self, time, current,mva, ref_state):
        self.time = time
        self.orig_current = current
        self.moving_average = mva
        self.reference_state = ref_state
        
        self.state_filter_time = self.reference_state.ref_time
        self.state_filter_current = self.reference_state.ref_curr
        
        self.interval = 0
        self.differential_order = self._get_diff_order()
        self.params_array = []
        
        self.percent_complete = 0
        self.total_period = (len(self.time*1000) - len(self.reference_state.ref_time))/1000  
        
        self.output_values = pd.DataFrame()
        self.output_locations = []
        
        self.prev_cnt = 0
        
    def _get_diff_order(self):
                
        if self.reference_state.name == StateName.LED_10:
            diff_order_value = 25
        elif self.reference_state.name == StateName.UL_ACT:
            diff_order_value = 25
        elif self.reference_state.name == StateName.UL_MAC:
            diff_order_value = 15
        else: 
            diff_order_value = 25
            
        return diff_order_value

    def correlate_signal(self, interval_inc_count):
        """ Correlate a section of the original signal against the reference state graph

        :param interval_inc_count: shift value for the reference window to move across the orignal signal
        :type interval_inc_count: float
        :return: Returns True if end of file is reached, otherwise False
        :rtype: bool
        """
        self.state_filter_time += self.interval  - round(self.state_filter_time[0], 3) # remove offset and add interval
        self.interval += interval_inc_count
        
        try:
            # Setting the start and end point of comparison filter
            indmin = self.time.loc[self.time == round(self.state_filter_time[0],3)].index[0]
            
            # If End-of-File reached
            if indmin + len(self.state_filter_time) >= len(self.time):
                self.output_values = self._evaluate_found_states()
                self._reset_variables()
                return True
            else:
                indmax = self.time.loc[self.time == round(self.state_filter_time[-1],3)].index[0]
        except IndexError as error:
            # print(f"INDEX_NOT_FOUND: {error}")
            return False
        
        # Extract the corresponding section of the graph from the measured device graph
        region_x = self.time[indmin:indmax + 1]
        region_y = self.moving_average[indmin:indmax + 1]    
        
        ref_state = pd.DataFrame(self.reference_state.ref_curr)[0]
        orig_state = pd.DataFrame(region_y)['Current']
        
        # Calculations for comparison -> Denoising Orignal Signal, Euclidean Distance, Correlation Shifting, Variance, Amplitude
        denoised_orig_state = Measurement.denoise_signal(region_x, orig_state, indmin)
        euc_d = Measurement.calculate_euc_distance_signals(ref_state, denoised_orig_state)        
        correlation = Measurement.calculate_correlation(ref_state, denoised_orig_state)        
        variance = Measurement.calculate_variance(denoised_orig_state)  
        amplitude = Measurement.calculate_amplitude(denoised_orig_state)  

        # DEBUG: Logging progress of analysis
        self.percent_complete = round((self.interval/self.total_period)*100)
        self._print_loading_bar()
        
        # print(f"[{self.percent_complete}%]: "
        #       f"{round(euc_d, 5)} , "
        #       f"{round(correlation, 5)} , "
        #       f"{round(variance,5)} , "
        #       f"{round(amplitude,5)}")
        
        # Add params to array for evaluation
        self.params_array.append([indmin, indmax, euc_d, correlation, round(variance,5), round(amplitude,5)])
        
        return False
    
    def _print_loading_bar(self):     
        """ Console logging of the evaluation progress during correlation analysis
        """   
        eq_str = "="
        bar_cnt = round(self.percent_complete/10)
        
        if self.prev_cnt == bar_cnt:
            return
        
        for i in range(bar_cnt):
            eq_str += "=="
            
        self.prev_cnt = bar_cnt
        print(f"{eq_str}[{self.percent_complete}%]")
    
    def _evaluate_found_states(self):
        """ Evaluate the parameters array for each correlation window
        
        Parameters Description:
         - Euc-D - Euclidean Distance; computed distance of each point between two signals (for evaluating most similar signal with least distance)
         - Correlation - Shifted values of the reference signal across the original signals (for evaluating signal with highest correlation value)
         - Variance - Overall variance of the signal (for evaluating straight lines vs fluctuating)
         - Amplitude - Maximum amplitude reached by the denoised current window graph (for evaluating fluctuating and high amplitude graph windows)
        
        Decision logic: 
        1. Finds the minimas of the array -> minima values will be coverging to the best Euc-D match.
        2. Compares with usual/accepted threshold values for each state (set with manual analysis) with each detected minima
        3. Calculates the average current and time delta
        4. Evalutes the average current against expected (for measuring current regression)
        5. Stores the evaluated state in the output table

        :return: All the found/detected states
        :rtype: pandas.DataFrame()()
        """
        found_states = pd.DataFrame()
        
        euc_vals = np.array([euc[2] for euc in self.params_array])
        corr_vals = np.array([corr[3] for corr in self.params_array])
        vari_vals = np.array([vari[4] for vari in self.params_array])
        amp_vals = np.array([amp[5] for amp in self.params_array])
        
        # Find minimum values of function
        minimas = argrelextrema(euc_vals, np.less,order=self.differential_order)[0]
        maximas = argrelextrema(corr_vals, np.greater,order=self.differential_order)[0]
        
        for min_idx in minimas:
            euc_val = euc_vals[min_idx]
            corr_val = corr_vals[min_idx]
            vari_val = vari_vals[min_idx]
            amp_val = amp_vals[min_idx]
            
            print(f"[DEBUG_LOG] minimia: {euc_val} , {corr_val}, {vari_val}, {amp_val}")
            
            # Error checking, atleast 5 values for minima converging
            if min_idx < 5:
                continue
            
            indmin = self.params_array[min_idx][0]
            indmax = self.params_array[min_idx][1]
            
            skip_value, state_label, euc_thresh, corr_thresh, vari_thresh = self._get_param_values(vari_val, amp_val)
            
            # Some values are skipped if the parameters do not meet the minimum requirements
            if skip_value:
                continue
            
            # Parameters should be within threshold range
            if euc_val < euc_thresh and corr_val > corr_thresh and vari_val <= vari_thresh:
                    self.avg_curr = self.orig_current[indmin:indmax].mean()
                    self.time_delta = round(self.time[indmax] - self.time[indmin],4)
                    print(f"AvgCurr: {self.avg_curr*1000}mA , TimeDelta: {self.time_delta}s")
                    
                    time_d = round(self.time_delta,2)
                    avg_curr = round(self.avg_curr * 1000, 2)
                    expected_curr = round(self.reference_state.ref_curr.mean() * 1000, 2)

                    if self._is_within_range(avg_curr, expected_curr,0.2): 
                        status = "LOW"
                    elif self._is_within_range(avg_curr, expected_curr,0.5): 
                        status = "MEDIUM"
                    elif self._is_within_range(avg_curr, expected_curr,0.7): 
                        status = "HIGH"
                    else:
                        status = "VERY HIGH"
                    
                    # Create a DataFrame row with the results
                    new_output_row  = pd.DataFrame({
                        'State_Name': [state_label],
                        'Average_Current(mA)': [avg_curr],
                        'Expected_Current(mA)': [expected_curr],
                        'Time_Delta(s)': [time_d],
                        'Status': [status]
                    })
                    # Append the new values to the existing DataFrame
                    found_states = pd.concat([found_states, new_output_row], ignore_index=True)
                    self.output_locations.append([indmin, indmax])
                    
        return found_states
            
    def _reset_variables(self):
        """ Reset all variables for next correlation cycle
        """
        self.interval = 0
        self.params_array = []
        self.is_eof = True
        
    def _get_param_values(self, vari_val, amp_val):
        """ Get the threshold values for corresponding state and evaluate minimum requirements
        
        Two requirements are checked; variance and amplitude, to avoid the false detection of straight lines
        as the matching state.

        :param vari_val: variance value for the selected window
        :type vari_val: float
        :param amp_val: amplitude value for the selected window
        :type amp_val: float
        :return: skip flag, state label and all required parameters for evaluation
        :rtype: bool, str, float, float, float
        """
        skip_value = False

        if self.reference_state.name  == StateName.LED_5:
            state_label = self.reference_state.name.name
            euc_thresh = 0.25
            corr_thresh = 0.04
            vari_thresh = 0.00002         
            # amp 0.002, var 0.008 analyze minimas further
            if amp_val <= 0.001:
                skip_value = True
        
        if self.reference_state.name  == StateName.LED_10:
            state_label = self.reference_state.name.name
            euc_thresh = 0.25
            corr_thresh = 0.01 # 0.1 -> check params
            vari_thresh = 0.00002         
            # amp 0.002, var 0.008 analyze minimas further
            if amp_val <= 0.001:
                skip_value = True
                
        if self.reference_state.name == StateName.WIFI_SCAN:      
            state_label = "WIFI_SCAN"
            euc_thresh = 2.0
            corr_thresh = 20.0
            vari_thresh = 0.0005  
            
            if vari_val == 0.0:
                skip_value = True
            
        if self.reference_state.name == StateName.UL_MAC:
            state_label = "UL_MAC"  
            euc_thresh = 0.3 
            corr_thresh = 0.1
            vari_thresh = 0.000015 
            
            if vari_val == 0.0:
                skip_value = True
                
            if amp_val >= 0.00390: #prev: 360
                skip_value = True
        
        if self.reference_state.name == StateName.UL_ACT:
            state_label = "UL_ACT"  
            euc_thresh = 0.35 
            corr_thresh = 0.1
            vari_thresh = 0.00002
            
            if vari_val == 0.0:
                skip_value = True
        
        if self.reference_state.name == StateName.UL_DLRQ:
            state_label = "UL_DLRQ"  
            euc_thresh = 1.0
            corr_thresh = 0.1
            vari_thresh = 0.00005
        else:
            if amp_val == 0:
                skip_value = True
            #[TODO]:implement orig vs ref amp comparison
        
        return skip_value, state_label, euc_thresh, corr_thresh, vari_thresh
    
    def _is_within_range(self, avg_curr, expected_curr, acceptable_range=1.0): #within 100% of value
        """ Check if the current value is within the accepted range of the reference

        :param avg_curr: average current of the measurement window
        :type avg_curr: float
        :param expected_curr: expected average current value of reference window
        :type expected_curr: float
        :param acceptable_range: within certain percantage of original, defaults to 1.0
        :type acceptable_range: float, optional
        :return: returns True if within range, otherwise False
        :rtype: bool
        """
        difference = avg_curr - expected_curr
        
        # print(difference/expected_curr)
        
        if difference < 0:
            return True
        
        if (difference/expected_curr) <= acceptable_range:
            return True
        
        # if -acceptable_range <= (difference/expected_curr) <= acceptable_range:
        #     return True
        
        return False
    
    def get_output_table(self):
        """ Seperates the location indices to different columns and returns the output tables

        :return: output values containing start and end index, state name, average and expected
                 current and the time delta
        :rtype: pandas.DataFrame()
        """
        self.output_values["indmin"] = [value[0] for value in self.output_locations]
        self.output_values["indmax"] = [value[1] for value in self.output_locations]
        
        return self.output_values

import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
import os
class CurrentGraphPlotter:
    """ Represents the plotting logic for current measurement and detected states

    :param states: Detected states and their indices
    :type states: pandas.DataFrame()
    :param current_output_filename: name of the current measurement file
    :type current_output_filename: str
    :param file_index: index of the file (to assign the graph to the test case)
    :type file_index: int
    :param data_folder: location of the current measurement file, defaults to "static/current_measurement/"
    :type data_folder: str, optional
    """
    def __init__(self, states, current_output_filename, file_index, folder_name, data_folder="static/current_measurement/"):
        ### Main data file to assess
        data_filename = data_folder + current_output_filename
        self.result_folder = folder_name
        self.data = pd.read_csv(f'{data_filename}')
        self._format_data()
        
        self.states = states
        
        # Plot variables
        self.fig, self.ax = plt.subplots(figsize=(12,4)) 
        self.ax.plot([],[]) 
        
        self.image_count = file_index
    
    def plot_graph_with_labelled_states(self):
        """ Call the helper plotting functions to plot and save the final labelled graph
        """
        self._plot_main_graph()
        self._plot_labelled_states()
        self._save_image()
        
        # plt.show()
        
    def _plot_main_graph(self):
        """ Plot a smoothed current graph from the original current measurement values (using moving average)
        """
        # Create a figure and axes 
        self.ax.set_title('Current vs. Time with Moving Average') 
        self.fig.patch.set_color('#EAFFF5')        
        
        # Set up graph, format axes
        scale_y = 1e3
        ticks_y = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x*scale_y))
        
        self.ax.set_xlabel('Time(s)')
        self.ax.set_ylabel('Current(mA)')
        self.ax.yaxis.set_major_formatter(ticks_y)
        
        self._plot_moving_average()
        
        plt.grid(True)
        plt.legend()
        
    def _plot_labelled_states(self):
        """ Plot an overlay of the detected state on top of the original current graph
        """
        self.states.reset_index(drop=True, inplace=True)
        for index, state in self.states.iterrows():
            # Adjusting label locations for better visibility
            if index % 2 == 0:
                offset = 0.12 * 2
            else:
                offset = 0.12
                    
            indmin = state['indmin']
            indmax = state['indmax']
            found_state = state['State_Name']
            
            color = self._set_state_color(found_state)
            
            self.ax.plot(self.time[indmin:indmax],self.moving_average[indmin:indmax], color=color)
            self.ax.text(self.time[indmin + round((indmax - indmin)/2)], 
                                self.moving_average.max() - offset*self.moving_average.max(), 
                                found_state, 
                                fontsize=10, 
                                # fontweight='semibold',
                                color='cyan', 
                                backgroundcolor='black',
                                horizontalalignment='center')
            
            self.fig.canvas.draw()
            
    def _set_state_color(self, state):
        plot_colors = ['red', 'blue', 'orange', 'purple', 'cyan', 'magenta', 'yellow']

        if state == "LED_5":
            color = plot_colors[0]
        if state == "LED_10":
            color = plot_colors[0]
        if state == "UL_ACT":
            color = plot_colors[2]
        if state == "UL_DLRQ":
            color = plot_colors[2]
        if state == "UL_MAC":
            color = plot_colors[2]
        if state == "WIFI_SCAN":
            color = plot_colors[1]
            
        return color
            
    def _save_image(self):
        """ Save graph as png image
        """
        self.fig.savefig(f'{self.result_folder}/output_figure_{self.image_count}.png')
                         
    def _format_data(self): 
        """ Adjust data to correct format before plotting
        """
        # Conversion for PPK generated values
        self.data['Current'] = self.data['Current'].div(1000000) #from uA to A
        self.data['Time'] = self.data['Time'] - self.data['Time'][0] #Remove offset
        self.data['Time'] = self.data['Time'].div(1000) # from ms to s
            
        # Set data for for calculations
        self.orig_data = self.data
        self.data = self.data.reset_index(drop=True)
        
        # Extract the 'Time' and 'Current' columns
        self.time = self.data['Time']
        self.current = self.data['Current']
        
        # Round to 3 decimal places
        time_round_val = 1000.0
        self.time = self.time.mul(time_round_val)
        self.time = np.floor(self.time)
        self.time = self.time.div(time_round_val)
        
    def _plot_moving_average(self):
        """ Compute and plot the moving average current graph
        """
        mva_window = 100
        self.moving_average = self.current.rolling(window=mva_window).mean().fillna(0)
        self.moving_avg_line, = plt.plot(self.time, self.moving_average, linestyle='--', color='green', label=f'Moving Average (Window={mva_window})')
    
#########################################################################
###                 Analysis classes for tracking states              ###
#########################################################################
class ActivationAnalysis:
    """ Represents an analysis logic for activation states
    
    For eg: 
     - filtering out an additional LED_5 state within an LED_10 state
     - detecting a downlink request based on succesive uplink, rx and ack states
    """
    def __init__(self):
        pass
    
    def filter_output(output):
        """ Filters the states based on certain criteria of the activation sequence

        :param output: output values/detected states and their indices
        :type output: pandas.DataFrame()
        :return: filtered output values/states
        :rtype: pandas.DataFrame()
        """
        try:
            if output['State_Name'] is not None:
                led_10 = output[output['State_Name'] == 'LED_10']
                led_5 = output[output['State_Name'] == 'LED_5']
                ul_mac = output[output['State_Name'] == 'UL_MAC']
                ul_act = output[output['State_Name'] == 'UL_ACT']
                
                # Iterate through 'LED_5' states and check if their locs are within the 'LED_10' range
                for idx_5, led_5_row in led_5.iterrows():
                    for idx_10, led_10_row in led_10.iterrows():
                        if led_10_row['indmin'] <= led_5_row['indmin'] <= led_10_row['indmax'] \
                        or led_10_row['indmin'] <= led_5_row['indmax'] <= led_10_row['indmax']:
                            output = output.drop(idx_5)
                            
                # Iterate through 'UL_ACT' states and check if their locs are within the 'UL_MAC' range
                for idx_act, ul_act_row in ul_act.iterrows():
                    for idx_mac, ul_mac_row in ul_mac.iterrows():
                        if ul_mac_row['indmin'] <= ul_act_row['indmin'] <= ul_mac_row['indmax'] \
                        or ul_mac_row['indmin'] <= ul_act_row['indmax'] <= ul_mac_row['indmax']:
                            # output = output.drop(idx_mac)
                            output = output.drop(idx_act)
        except KeyError as ke:
            print(f"Column not found: {ke}. Dataframe is empty")
        
        output = output.sort_values(by='indmin')            
        return output
    
    
#########################################################################
###                 Measurement class for Calculations                ###
#########################################################################  
from scipy.spatial import distance

class Measurement:
    """ Contains helper functions for all kinds of calculations.
    
    Functions available:
    - Format Current - formats current value to appropriate current decimal and unit string
    - Fourier/Inverse-Fourier - computes FFT and IFFT of the signal
    - Denoise Signal - denoises the signal using FFT/IFFT logic
    - Euclidean Distance - calculates the euc-d between two signals
    - Correlation - calculates the correlation between two signals
    - Variance - calculates the variance in a signal
    - Amplitude - calculates the maximum amplitude in a signal
    """
    def __init__(self):
        pass
    
    def format_current(value, unit='A'):
        """ Format to appropriate decimal value and unit

        :param value: current value
        :type value: float
        :param unit: unit of measurement, defaults to 'A'
        :type unit: str, optional
        :return: formatted string with units
        :rtype: str
        """
        units = {
            'A': (1, 'A'),
            'mA': (1e-3, 'mA'),
            'uA': (1e-6, 'uA'),
            'nA': (1e-9, 'nA')
        }
        
        # Find the appropriate unit
        for base_unit, (scale, unit_name) in units.items():
            if abs(value) >= scale:
                formatted_value = value / scale
                return f'{formatted_value:.4f} {unit_name}'
        
        # If the value is too small, default to nA
        formatted_value = value / units['nA'][0]
        return f'{formatted_value:.4e} nA'
    
    def calculate_ftt(region_x, region_y, indmin):
        """ Calculate the Fourier Transform from time domain to frequency domain of the signal

        :param region_x: x values of window
        :type region_x: pandas.Series()
        :param region_y: y values of window
        :type region_y: pandas.Series()
        :param indmin: starting index of series, needed to compute dt (minimum delta between values)
        :type indmin: int
        :return: Fourier transform result values, frequency values and Power spectrum diagram (PSD) values
        :rtype: numpy.array(), numpy.array(), numpy.array()
        """
        n = len(region_x)
        dt = region_x[indmin+1] - region_x[indmin]
        dt = max(0.001, dt)      
            
        fft_result = np.fft.fft(region_y)
        fft_freq = np.fft.fftfreq(len(region_x), dt)
        
        PSD = fft_result * np.conj(fft_result) / n
        
        return fft_result, fft_freq, PSD
    
    def calculate_iftt(fft_result, PSD, PSD_thresh):
        """Calculate the inverse Fourier Transform from frequency domain to time domain of the signal

        :param fft_result: Fourier transform result values
        :type fft_result: numpy.array()
        :param PSD: Power spectrum diagram (PSD) values
        :type PSD: numpy.array()
        :param PSD_thresh: Power Spectrum Diagram threshold (used to filter out smaller peaks as noise)
        :type PSD_thresh: float
        :return: Inverse fourier transform signal, filtered PSD values
        :rtype: numpy.array(), numpy.array()
        """
        indices = PSD > PSD_thresh # Filter out the smaller peaks 
        PSDclean = PSD * indices # Convulate the values to zero
        PSDclean[0] = 0 # Filter out the zero peak
        fft_result = indices * fft_result # Remove zero elements from original signal (filtering)
        ifft_result = np.fft.ifft(fft_result) 
        
        return ifft_result, PSDclean
    
    def denoise_signal(region_x, region_y, indmin, PSD_thresh=0.001):
        """ Call the Fourier and Inverse Fourier transform functions to denoise a signal

        :param region_x: x values of window
        :type region_x: pandas.Series()
        :param region_y: y values of window
        :type region_y: pandas.Series()
        :param indmin: starting index of series, needed to compute dt (minimum delta between values)
        :type indmin: int
        :param PSD_thresh: Power Spectrum Diagram threshold (used to filter out smaller peaks as noise), defaults to 0.001
        :type PSD_thresh: float, optional
        :return: Denoised signal 
        :rtype: numpy.array()
        """
        fft_result, fft_freq, PSD = Measurement.calculate_ftt(region_x, region_y, indmin)
        ifft_result, PSDclean = Measurement.calculate_iftt(fft_result, PSD, PSD_thresh)
        signal = np.real(ifft_result)
        
        return signal
        
    def calculate_correlation(r_state, o_state):
        """ Compares two states by shifting the reference state across the orignal and computing maximum correlation fit
            [ref: https://makeabilitylab.github.io/physcomp/signals/ComparingSignals/index.html]

        :param r_state: reference state window
        :type r_state: pandas.Series()
        :param o_state: orignal state window
        :type o_state: pandas.Series()
        :return: correlation value generated by numpy correlate function
        :rtype: float
        """
        a = o_state
        b = r_state
        
        padding_length = len(a) - len(b)
        
        if padding_length > 0:
            a = a[:-padding_length]
        elif padding_length < 0:
            a = np.pad(a, (0, np.abs(padding_length)), mode = 'constant', constant_values=0)
        
        correlate_result = np.correlate(a, b, 'full')

        return correlate_result[correlate_result.argmax()]
        
    def calculate_variance(state):
        """ Calculate the variance in a signal

        :param state: signal window
        :type state: pandas.Series()
        :return: variance value
        :rtype: float
        """
        variance = np.var(state)
        # variance = round(np.var(state), 5)
        return variance
    
    def calculate_amplitude(state):
        """ Calculate the maxmium amplitude reached by the signal

        :param state: signal window
        :type state: pandas.Series()
        :return: amplitude value
        :rtype: float
        """
        amplitude = max(state) - state.mean()
        # amplitude = round(max(state) - state.mean(), 5)
        return amplitude
        
    def calculate_euc_distance_signals(r_state, o_state):
        """ Calculates the euclidean distance between two signals
            [ref: https://makeabilitylab.github.io/physcomp/signals/ComparingSignals/index.html] 

        
        :param r_state: reference state window
        :type r_state: pandas.Series()
        :param o_state: orignal state window
        :type o_state: pandas.Series()
        :return: euclidean distance value generated by scipy distance class function
        :rtype: float
        """
        a = o_state
        b = r_state
        
        padding_length = len(a) - len(b)
        
        if padding_length > 0:
            a = a[:-padding_length]
            # b = np.pad(b, (0, np.abs(padding_length)), mode = 'constant', constant_values=0)
        elif padding_length < 0:
            a = np.pad(a, (0, np.abs(padding_length)), mode = 'constant', constant_values=0)
        
        return distance.euclidean(a, b)
    
if __name__ == "__main__":
    new_CD = CurrentDetector("LED_10", "output_ppk2.csv", data_folder="../current_logs/", ref_folder="../ref_current_graphs/")
    new_CD.run_current_detector()