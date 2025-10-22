import time
import yaml
import datetime
from NSTA.testscripts.test_script import TestScript
from NSTA.interface.sensolus_web_interface import SensolusWebInterface
from NSTA.devices.platform_device import PlatformDevice


class Hati_Utils(PlatformDevice):
    def __init__(self):
        super().__init__(name="HATI Device", device_id="")  # Initialize the base class
        #self.interface = SensolusWebInterface()
        self.connect()
        self._load_configuration()  # Load device_id from configuration

        if self.device_id:  # Only construct URLs if device_id is valid
            self.get_url = f"/rest/device_usage_profile/{self.device_id}/getByDevice"
            self.post_url = f"/rest/device_setting_queue/saveProfileAndCategories/{self.device_id}"
            self.upcoming_setting_url = f"/rest/device_setting_queue/upcomingSetting/{self.device_id}"
        else:
            self.logger.info("%s","Warning: Device ID is missing or invalid")

    def _load_configuration(self):
        # Load configuration from YAML file
        config_file = "../NSTA/config/teststation_config.yaml"
        with open(config_file, 'r') as file:
            config = yaml.safe_load(file)
            if config is None or 'device' not in config:
                self.logger.info("%s",f"Warning: Configuration file '{config_file}' is empty or missing 'device' key.")
                return

            # Extract the device_id from the nested structure
            device_config = config['device']
            if not isinstance(device_config, list) or len(device_config) == 0:
                self.logger.info("%s","Warning: The 'device' key should be a list with at least one item.")
                return

            parameters = device_config[0].get('parameters', {})
            self.device_id = parameters.get('device_id')  # Set device_id from config
            self.profile_id = parameters.get('profile_id')  # Set profile_id from config

            if not self.device_id:
                self.logger.info("%s","Warning: device_id is not defined in the configuration")

    def _get_current_ts_utc(self):
        """Returns the current UTC timestamp in ISO 8601 format."""
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    def fetch_profile_details(self, profile_id):
        response = self.interface.get(self.get_url)
        
        if response:
            if isinstance(response, list):
                profile = next((item for item in response if item.get('id') == profile_id), None)
            elif isinstance(response, dict) and response.get('id') == profile_id:
                profile = response
            else:
                return None, None, False
            
            if profile:
                categories_options = {
                    category['name']: [option['name'] for option in category.get('options', [])]
                    for category in profile.get('categories', [])
                }
                
                # Check if "keep alive 1hour" category is present
                keep_alive_present = any(cat['name'] == "keep alive 1hour" for cat in profile.get('categories', []))
                
                return profile, categories_options, keep_alive_present
            else:
                return None, None, False
        else:
            return None, None, False

    def post_profile_settings(self, profile_id, apply_categories):
        post_data = {
            "profile": {
                "id": profile_id,
                "name": "HATI Test Team"
            },
            "applyCategory": apply_categories
        }
        
        #self.logger.info("%s",f"POST Request URL: {self.post_url}")
        #self.logger.info("%s",f"POST Request Body: {post_data}")

        response = self.interface.post(self.post_url, data=post_data)
        
        if response:
            self.logger.info("%s",f"POST Keep Alive Request succeeded.")
            return True
        else:
            self.logger.info("%s",f"POST Request failed. Status Code: {response.status_code}, Response content: {response.text}")
            return False

    def get_applied_device_usage_profile(self):
        """Get the upcoming settings to retrieve the applied device usage profile."""
        response = self.interface.get(self.upcoming_setting_url)
        
        if response:
            applied_profile = response.get('deviceSettings', {}).get('appliedDeviceUsageProfile', {})
            return applied_profile
        return None

    def get_frames(self, start_time_utc, end_time_utc, max_n_frames=150):
        """Retrieve messages between the specified time range."""
        current_utc_time_dt = datetime.datetime.utcnow()
        
        # Ensure date format is in ISO 8601 with timezone info
        if end_time_utc:
            end_time_utc_url = f"{end_time_utc}+00:00"
        else:
            end_time_utc_url = current_utc_time_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        
        if start_time_utc:
            start_time_utc_url = f"{start_time_utc}+00:00"
        else:
            start_time_utc_dt = current_utc_time_dt - datetime.timedelta(days=1)
            start_time_utc_url = start_time_utc_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")

        # Log the request parameters for debugging
        #self.logger.info("%s",f"Requesting frames from {start_time_utc_url} to {end_time_utc_url} with max {max_n_frames} frames")

        try:
            response = self.interface.get(f"/rest/sigfoxdevices/{self.device_id}/sigfoxMessages", parameters={
                'start': 0,
                'limit': max_n_frames,
                'from_date': start_time_utc_url,
                'to_date': end_time_utc_url,
                'not_filter': False
            })
            if response.get("message", "") == "no_data_in_time_filter_key":
                self.logger.info("%s","No data frames within given time window!")
            return response.get("data", [])
        except ValueError as e:
            self.logger.info("%s",f"Error while fetching frames: {e}")
            return []

    def check_bidir_ack(self, start_time, end_time):
        """Check for BIDIR ACK within the specified time range."""
        messages = self.get_frames(start_time_utc=start_time, end_time_utc=end_time)
        boot_message = None
        
        # self.logger.info "%s",the raw backend messages for debugging
        #self.logger.info("%s","Backend Messages:")
        #for message in messages:
        #    self.logger.info("%s",message)
        
        for message in messages:
            for data_message in message.get("data", []):
                if 'decodedMsg' in data_message and data_message["decodedMsg"].get("messageType") == "BIDIR_ACK":
                    boot_message = data_message.copy()
                    break
            if boot_message:
                break
        
        if boot_message:
            self.logger.info("%s","BIDIR ACK received.")
            return True
        
        self.logger.info("%s","BIDIR ACK not found in messages.")
        return False

class HATI_Config_Settings(TestScript):

    def __init__(self):
        super().__init__()
        self.name = "HATI_Cofig_Settings"
        self.automation_content = "HATI_Cofig_Settings"
        self.version = 0.1
        # self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 3

    def teststeps(self):
        # Step 1: Send Keep Alive 1 hour
        start_time = Hati_Utils()._get_current_ts_utc()
        if not Hati_Utils().post_profile_settings(Hati_Utils().profile_id, [{"categoryName": "keep alive 1hour", "optionName": "Keep alive"}]):
            self.logger.info("%s","Failed to send Keep Alive request.")
            self.logger.info("Step 1: %s", "Failed to send Keep Alive request.")
            return
        self.logger.info("%s", "Keep Alive request successful.")
        
        self.logger.info("%s", "Wait for 1 hr")
        time.sleep(180)  # Wait for 5 minutes
        
        end_time = Hati_Utils()._get_current_ts_utc()
        
        # Check for BIDIR ACK
        if not Hati_Utils().check_bidir_ack(start_time, end_time):
            self.logger.info("%s",f"BIDIR ACK not received for Keep Alive request.")
            return
        
        applied_profile = Hati_Utils().get_applied_device_usage_profile()
        
        if not applied_profile:
            self.logger.info("%s","Failed to retrieve applied device usage profile.")
            return
        
        categories_options = {
            category['name']: [option['name'] for option in category.get('options', [])]
            for category in applied_profile.get('categories', [])
        }
        
        self.logger.info("%s","Retrieved Categories and Options:")
        for category_name, options in categories_options.items():
            self.logger.info("%s",f"Category: {category_name}")
            for option in options:
                self.logger.info("%s",f"  Option: {option}")
        
        # Iterate through each category and its options
        categories = list(categories_options.keys())
        num_categories = len(categories)
        
        step_count_n = 0
        # Loop through each category
        for i in range(num_categories):
        #for i in range():
            current_category_name = categories[i]
            current_category_options = categories_options[current_category_name]
            
            # Loop through each option in the current category
            for option in current_category_options:
                # Prepare the post data for this combination
                apply_categories = []

                # Set default options for other categories
                for j in range(num_categories):
                    if i == j:
                        apply_categories.append({"categoryName": current_category_name, "optionName": option})
                    else:
                        default_option = categories_options[categories[j]][0]  # Choosing the first option as default
                        apply_categories.append({"categoryName": categories[j], "optionName": default_option})

                # Send POST request with current option for the category
                self.logger.info("%s",f"Sending POST request for category '{current_category_name}' with option '{option}'...")
                step_description = f"Sending POST request for category '{current_category_name}' with option '{option}'..."
                expected_result = f"Sent POST request succesfully for category '{current_category_name}' with option '{option}'..."
                actual_result = ""
                start_time = Hati_Utils()._get_current_ts_utc()
                if not Hati_Utils().post_profile_settings(Hati_Utils().profile_id, apply_categories):
                    self.logger.info("%s",f"Failed to send POST request for category '{current_category_name}' with option '{option}'.")
                    actual_result = f"Failed to send POST request for category '{current_category_name}' with option '{option}'."
                    step_verdict = self.result_classifier.FAILED
                    self.save_step(step_count_n+1, step_description, expected_result, actual_result, step_verdict)
                    return
                actual_result = f"Send POST request successfully for category '{current_category_name}' with option '{option}'."
                step_verdict = self.result_classifier.PASSED
                self.save_step(step_count_n+1, step_description, expected_result, actual_result, step_verdict)

                # Wait for 5 minutes before checking BIDIR ACK
                self.logger.info("%s",f"Waiting for 60 minutes before checking BIDIR ACK...")
                time.sleep(200)

                end_time = Hati_Utils()._get_current_ts_utc()

                # Check for BIDIR ACK
                step_description = f"Check BIDIR ACK for category '{current_category_name}' with option '{option}'."
                expected_result = f"BIDIR ACK received for category '{current_category_name}' with option '{option}'"
                actual_result = ""
                if not Hati_Utils().check_bidir_ack(start_time, end_time):
                    self.logger.info("%s",f"BIDIR ACK not received for category '{current_category_name}' with option '{option}'. Test failed.")
                    actual_result = f"BIDIR ACK not received for category '{current_category_name}' with option '{option}'"
                    step_verdict = self.result_classifier.FAILED
                    self.save_step(step_count_n+2, step_description, expected_result, actual_result, step_verdict)
                    return
                actual_result = f"BIDIR ACK received for category '{current_category_name}' with option '{option}'"
                step_verdict = self.result_classifier.PASSED
                self.save_step(step_count_n+2, step_description, expected_result, actual_result, step_verdict)

                time.sleep(30)  # Wait for 1 minute
                step_count_n += 2

# if __name__ == "__main__":
#     pm = HatiTestConfig()
#     pm.run()