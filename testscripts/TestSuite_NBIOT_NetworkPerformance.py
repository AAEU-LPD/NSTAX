"""Test Suite for Platform NB-IoT Netwrok Performance stats."""


from NSTAX.testscripts.test_script import TestScript


class NBIOT_NBDiag_AllECL(TestScript):
    """Check ECL Levels From All NBIOT_DIAGNOSTIC messages.
    Works on any device types with NB-Iot over platform.

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Works with N5, T1100
    """
    def __init__(self):
        super().__init__()
        self.name = "NBIOT_NBDiag_AllECL"
        self.automation_content = "NBIOT_NBDiag_AllECL"
        self.description = "Check ECL Statistics form NBIOT_DIAGNOSTIC"
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 7
        self.version = 0.1

    def teststeps(self):
        # Step 0: Get test parameters
        test_parameters = self.params_from_testcfg
        start_time_utc = test_parameters.get("start_time_utc")
        end_time_utc = test_parameters.get("end_time_utc")
        max_message_count = test_parameters.get("max_message_count")

        # Step 1: Retrieve device messages from platform
        step_description = "Retrieve diagnostic messages"
        expected_result = "#dataframes_received > 10"
        self.logger.info("Step 1: %s", step_description)
        # backend_messages_t = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_messages=max_message_count)
        backend_dataframes = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_frames=max_message_count)
        n_backend_dataframes = len(backend_dataframes)
        actual_result = f"#dataframes_received: {n_backend_dataframes}"
        step_verdict = self.result_classifier.PASSED if n_backend_dataframes > 10 else self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        # Stop next steps if this step fails
        if step_verdict == self.result_classifier.FAILED:
            self.logger.error("Step failed, skipping remaining steps")
            return

        # Step 2: Check for valid net stats
        step_description = "Net stats data validity"
        expected_result = "#dataframes_received == #net_stats"
        self.logger.info("Step 2: %s", step_description)
        # Check net data availability
        net_data_list = []
        for dataframe in backend_dataframes:
            net_data_list_t = dataframe.get("networks", [])
            for net_data_t in net_data_list_t:
                try:
                    net_data_t["decodedMsg"]["data"]["ecl"]
                    net_data_list.append(net_data_t)
                    break       # Found net data, continue with next frame
                except KeyError:
                    continue    # Not net data, continue with next network element
        n_net_data = len(net_data_list)
        actual_result = f"#net_stats: {n_net_data}"
        step_verdict = self.result_classifier.PASSED if n_backend_dataframes == n_net_data else self.result_classifier.FAILED
        self.save_step(2, step_description, expected_result, actual_result, step_verdict)

        # Stop next steps if this step fails
        if step_verdict == self.result_classifier.FAILED:
            self.logger.error("Step failed, skipping remaining steps")
            return

        # Get ECL stats
        ecl_counter = {
            0: 0,
            1: 0,
            2: 0,
            255: 0,
            "INVALID_VALUE": 0,
            "DECODER_ERROR": 0
        }
        for net_data in net_data_list:
            try:
                meas_ecl = int(net_data["decodedMsg"]["data"]["ecl"])
            except KeyError:
                ecl_counter["DECODER_ERROR"] += 1
            except ValueError:
                ecl_counter["INVALID_VALUE"] += 1
            else:
                if meas_ecl in ecl_counter:
                    ecl_counter[meas_ecl] += 1
                else:
                    ecl_counter["INVALID_VALUE"] += 1

        # Step 3: Check ECL 0 occurrances
        step_description = "Check ECL 0 occurrances"
        expected_result = "#ECL0_counter > 80%"
        self.logger.info("Step 3: %s", step_description)
        p_ecl_counter = int(100 * ecl_counter[0] / n_net_data)
        actual_result = f"#ECL0_counter = {p_ecl_counter}% ({ecl_counter[0]} / {n_net_data})"
        step_verdict = self.result_classifier.PASSED if p_ecl_counter > 80 else self.result_classifier.FAILED
        self.save_step(3, step_description, expected_result, actual_result, step_verdict)

        # Step 4: Check ECL 1 occurrances
        step_description = "Check ECL 1 occurrances"
        expected_result = "#ECL1_counter < 20%"
        self.logger.info("Step 4: %s", step_description)
        p_ecl_counter = int(100 * ecl_counter[1] / n_net_data)
        actual_result = f"#ECL1_counter = {p_ecl_counter}% ({ecl_counter[1]} / {n_net_data})"
        step_verdict = self.result_classifier.PASSED if p_ecl_counter < 20 else self.result_classifier.FAILED
        self.save_step(4, step_description, expected_result, actual_result, step_verdict)

        # Step 5: Check ECL 2 occurrances
        step_description = "Check ECL 2 occurrances"
        expected_result = "#ECL2_counter < 10%"
        self.logger.info("Step 5: %s", step_description)
        p_ecl_counter = int(100 * ecl_counter[2] / n_net_data)
        actual_result = f"#ECL2_counter = {p_ecl_counter}% ({ecl_counter[2]} / {n_net_data})"
        step_verdict = self.result_classifier.PASSED if p_ecl_counter < 10 else self.result_classifier.FAILED
        self.save_step(5, step_description, expected_result, actual_result, step_verdict)

        # Step 6: Check ECL 255 occurrances
        step_description = "Check ECL 255 occurrances"
        expected_result = "#ECL255_counter < 10%"
        self.logger.info("Step 6: %s", step_description)
        p_ecl_counter = int(100 * ecl_counter[255] / n_net_data)
        actual_result = f"#ECL255_counter = {p_ecl_counter}% ({ecl_counter[255]} / {n_net_data})"
        step_verdict = self.result_classifier.PASSED if p_ecl_counter < 10 else self.result_classifier.FAILED
        self.save_step(6, step_description, expected_result, actual_result, step_verdict)

        # Step 7: Check Unknown/Bad ECL Readouts
        step_description = "Check Unknown/Bad ECL Readouts"
        expected_result = "#UNKNOWN_ECL_counter = 0"
        self.logger.info("Step 7: %s", step_description)
        n_bad_ecl_readout = ecl_counter["INVALID_VALUE"] + ecl_counter["DECODER_ERROR"]
        actual_result = f"#UNKNOWN_ECL_counter = {n_bad_ecl_readout}"
        if n_bad_ecl_readout:
            self.save_step(7, step_description, expected_result, actual_result, self.result_classifier.FAILED)
        else:
            self.save_step(7, step_description, expected_result, actual_result, self.result_classifier.PASSED)


class NBIOT_NBDiag_AllNetPerf(TestScript):
    """Check Network Level Performance Parameters.
    Works on any device types with NB-Iot over platform.

    TODO: Update expected performance parameters

    Pre-conditions:
        - Access to AlpsAlpine API Platform
        - Works with N5, T1100
    """
    def __init__(self):
        super().__init__()
        self.name = "NBIOT_NBDiag_AllNetPerf"
        self.automation_content = "NBIOT_NBDiag_AllNetPerf"
        self.description = "Check Network Statistics"
        self.requirement["DUT"].append("PlatformDevice")
        self.n_steps = 2
        self.version = 0.1

    def teststeps(self):
        # Step 0: Get test parameters
        test_parameters = self.params_from_testcfg
        start_time_utc = test_parameters.get("start_time_utc")
        end_time_utc = test_parameters.get("end_time_utc")
        max_message_count = test_parameters.get("max_message_count")

        # Step 1: Retrieve device messages from platform
        step_description = "Retrieve diagnostic messages"
        expected_result = "#dataframes_received > 10"
        self.logger.info("Step 1: %s", step_description)
        # backend_messages_t = self.DUT.get_messages(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_messages=max_message_count)
        backend_dataframes = self.DUT.get_frames(start_time_utc=start_time_utc, end_time_utc=end_time_utc, max_n_frames=max_message_count)
        n_backend_dataframes = len(backend_dataframes)
        actual_result = f"#dataframes_received: {n_backend_dataframes}"
        step_verdict = self.result_classifier.PASSED if n_backend_dataframes > 10 else self.result_classifier.FAILED
        self.save_step(1, step_description, expected_result, actual_result, step_verdict)

        # Stop next steps if this step fails
        if step_verdict == self.result_classifier.FAILED:
            self.logger.error("Step failed, skipping remaining steps")
            return

        # Step 2: Check for valid net stats
        step_description = "Net stats data validity"
        expected_result = "#dataframes_received == #net_stats"
        self.logger.info("Step 2: %s", step_description)
        # Check net data availability
        net_data_list = []
        for dataframe in backend_dataframes:
            net_data_list_t = dataframe.get("networks", [])
            for net_data_t in net_data_list_t:
                try:
                    net_data_t["decodedMsg"]["data"]["ecl"]
                    net_data_list.append(net_data_t)
                    break       # Found net data, continue with next frame
                except KeyError:
                    continue    # Not net data, continue with next network element
        n_net_data = len(net_data_list)
        actual_result = f"#net_stats: {n_net_data}"
        step_verdict = self.result_classifier.PASSED if n_backend_dataframes == n_net_data else self.result_classifier.FAILED
        self.save_step(2, step_description, expected_result, actual_result, step_verdict)

        # Stop next steps if this step fails
        if step_verdict == self.result_classifier.FAILED:
            self.logger.error("Step failed, skipping remaining steps")
            return

        PLMN_STAT_ALL = {}
        DATA_ERROR = 0

        # Crawl through net stats
        for net_data in net_data_list:
            try:
                meas_plmn = net_data["decodedMsg"]["data"]["operator"]
                meas_ecl = int(net_data["decodedMsg"]["data"]["ecl"])
                meas_sc_band = int(net_data["decodedMsg"]["data"]["sc_band"])
                meas_tx_pwr = float(net_data["decodedMsg"]["data"]["sc_tx_pwr"])
                meas_rsrp = meas_sc_band = int(net_data["decodedMsg"]["data"]["rsrp"])
                meas_rsrq = meas_sc_band = int(net_data["decodedMsg"]["data"]["rsrq"])
                meas_country_code = net_data["decodedMsg"]["operatorInfo"]["countryCode"]
                meas_operator = net_data["decodedMsg"]["operatorInfo"]["operator"]
            except (KeyError, ValueError):
                DATA_ERROR += 1
            if meas_operator not in PLMN_STAT_ALL:
                # For the very first occurrence of a PLMN
                PLMN_STAT_TEMPLATE = {
                    "country_code": "",
                    "frame_counter": 0,
                    "rsrp_stat": {
                        "excellent": 0,
                        "good": 0,
                        "fair_to_poor": 0,
                        "poor": 0,
                        "error_255": 0,
                        "INVALID_VALUE": 0
                    },
                    "rsrq_stat": {
                        "excellent": 0,
                        "good": 0,
                        "fair_to_poor": 0,
                        "poor": 0,
                        "error_255": 0,
                        "INVALID_VALUE": 0
                    },
                    "ecl_stat": {
                        0: 0,
                        1: 0,
                        2: 0,
                        255: 0,
                        "INVALID_VALUE": 0,
                    },
                    "tx_pwr_stat": {
                        "cat_1": 0,
                        "cat_2": 0,
                        "error_255": 0,
                        "INVALID_VALUE": 0,
                    },
                    "data": {
                        "sc_bands": [],
                        "sc_tx_pwrs": [],
                        "rsrps": [],
                        "rsrqs": [],
                        "ecls": [],
                    },
                }
                PLMN_STAT_ALL[meas_operator] = PLMN_STAT_TEMPLATE.copy()
                PLMN_STAT_ALL[meas_operator]["country_code"] = meas_country_code
            PLMN_STAT_ALL[meas_operator]["frame_counter"] += 1
            PLMN_STAT_ALL[meas_operator]["data"]["sc_bands"].append(meas_sc_band)
            PLMN_STAT_ALL[meas_operator]["data"]["sc_tx_pwrs"].append(meas_tx_pwr)
            PLMN_STAT_ALL[meas_operator]["data"]["rsrps"].append(meas_rsrp)
            PLMN_STAT_ALL[meas_operator]["data"]["rsrqs"].append(meas_rsrq)
            PLMN_STAT_ALL[meas_operator]["data"]["ecls"].append(meas_ecl)
            # Update Stats
            # Update ECL Stats
            if meas_ecl in (0, 1, 2, 255):
                PLMN_STAT_ALL[meas_operator]["ecl_stat"][meas_ecl] += 1
            else:
                PLMN_STAT_ALL[meas_operator]["ecl_stat"]["INVALID_VALUE"] += 1
            # Update RSRP Stats
            if meas_rsrp == 255:
                PLMN_STAT_ALL[meas_operator]["rsrp_stat"]["error_255"] += 1
            elif meas_rsrp >= -80:
                PLMN_STAT_ALL[meas_operator]["rsrp_stat"]["excellent"] += 1
            elif meas_rsrp >= -90:
                PLMN_STAT_ALL[meas_operator]["rsrp_stat"]["good"] += 1
            elif meas_rsrp >= -110:
                PLMN_STAT_ALL[meas_operator]["rsrp_stat"]["fair_to_poor"] += 1
            elif meas_rsrp >= -120:
                PLMN_STAT_ALL[meas_operator]["rsrp_stat"]["poor"] += 1
            else:
                PLMN_STAT_ALL[meas_operator]["rsrp_stat"]["INVALID_VALUE"] += 1
            # Update RSRQ Stats
            if meas_rsrq == 255:
                PLMN_STAT_ALL[meas_operator]["rsrq_stat"]["error_255"] += 1
            elif meas_rsrq >= -5:
                PLMN_STAT_ALL[meas_operator]["rsrq_stat"]["excellent"] += 1
            elif meas_rsrq >= -8:
                PLMN_STAT_ALL[meas_operator]["rsrq_stat"]["good"] += 1
            elif meas_rsrq >= -10:
                PLMN_STAT_ALL[meas_operator]["rsrq_stat"]["fair_to_poor"] += 1
            elif meas_rsrq >= -20:
                PLMN_STAT_ALL[meas_operator]["rsrq_stat"]["poor"] += 1
            else:
                PLMN_STAT_ALL[meas_operator]["rsrq_stat"]["INVALID_VALUE"] += 1
            # Update TX Power Stats
            if meas_tx_pwr == 255:
                PLMN_STAT_ALL[meas_operator]["tx_pwr_stat"]["error_255"] += 1
            elif meas_tx_pwr >= -5:
                PLMN_STAT_ALL[meas_operator]["tx_pwr_stat"]["cat_1"] += 1
            elif meas_tx_pwr < -5:
                PLMN_STAT_ALL[meas_operator]["tx_pwr_stat"]["cat_2"] += 1
            else:
                PLMN_STAT_ALL[meas_operator]["tx_pwr_stat"]["INVALID_VALUE"] += 1

        # Iterate over opearators
        current_test_step = 2
        for (plmn_number, plmn_container) in PLMN_STAT_ALL.items():
            meas_plmn = plmn_number
            meas_frame_counter = plmn_container["frame_counter"]

            # ECL Check
            # Step: Check ECL 0 occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #ECL0"
            expected_result = "#ECL0_counter > 80%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_ecl0 = plmn_container["ecl_stat"][0]
            p_ecl_counter = int(100 * n_ecl0 / meas_frame_counter)
            actual_result = f"#ECL0_counter = {p_ecl_counter}% ({n_ecl0}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_ecl_counter > 80 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check ECL 1 occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #ECL1"
            expected_result = "#ECL1_counter < 20%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_ecl1 = plmn_container["ecl_stat"][1]
            p_ecl_counter = int(100 * n_ecl1 / meas_frame_counter)
            actual_result = f"#ECL1_counter = {p_ecl_counter}% ({n_ecl1}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_ecl_counter < 20 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check ECL 2 occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #ECL2"
            expected_result = "#ECL2_counter < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_ecl2 = plmn_container["ecl_stat"][2]
            p_ecl_counter = int(100 * n_ecl2 / meas_frame_counter)
            actual_result = f"#ECL2_counter = {p_ecl_counter}% ({n_ecl2}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_ecl_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check ECL 255 occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #ECL255"
            expected_result = "#ECL255_counter < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_ecl255 = plmn_container["ecl_stat"][255]
            p_ecl_counter = int(100 * n_ecl255 / meas_frame_counter)
            actual_result = f"#ECL255_counter = {p_ecl_counter}% ({n_ecl255}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_ecl_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check ECL INVALID occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #ECL_INVALID"
            expected_result = "#ECL_INVALID_counter < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_ecl_inv = plmn_container["ecl_stat"]["INVALID_VALUE"]
            p_ecl_counter = int(100 * n_ecl_inv / meas_frame_counter)
            actual_result = f"#ECL_INVALID_counter = {p_ecl_counter}% ({n_ecl_inv}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_ecl_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # RSRP Check
            # Step: Check RSRP EXCELLENT or GOOD occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRP_EXCELLENT_OR_GOOD"
            expected_result = "#RSRP_EXCELLENT_OR_GOOD > 80%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrp_excellent_or_good = plmn_container["rsrp_stat"]["excellent"] + plmn_container["rsrp_stat"]["good"]
            p_rsrp_counter = int(100 * n_rsrp_excellent_or_good / meas_frame_counter)
            actual_result = f"#RSRP_EXCELLENT_OR_GOOD = {p_rsrp_counter}% ({n_rsrp_excellent_or_good}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrp_counter > 80 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRP RSRP_FAIR_TO_POOR occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRP_FAIR_TO_POOR"
            expected_result = "#RSRP_FAIR_TO_POOR < 50%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrp_fair_to_poor = plmn_container["rsrp_stat"]["fair_to_poor"]
            p_rsrp_counter = int(100 * n_rsrp_fair_to_poor / meas_frame_counter)
            actual_result = f"#RSRP_FAIR_TO_POOR = {p_rsrp_counter}% ({n_rsrp_fair_to_poor}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrp_counter < 50 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRP POOR occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRP_POOR"
            expected_result = "#RSRP_POOR < 20%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrp_poor = plmn_container["rsrp_stat"]["poor"]
            p_rsrp_counter = int(100 * n_rsrp_poor / meas_frame_counter)
            actual_result = f"#RSRP_POOR = {p_rsrp_counter}% ({n_rsrp_poor}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrp_counter < 20 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRP RSRP 255 occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRP_255"
            expected_result = "#RSRP_255 < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrp_255 = plmn_container["rsrp_stat"]["error_255"]
            p_rsrp_counter = int(100 * n_rsrp_255 / meas_frame_counter)
            actual_result = f"#RSRP_255 = {p_rsrp_counter}% ({n_rsrp_255}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrp_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRP INVALID occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRP_INVALID"
            expected_result = "#RSRP_INVALID < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrp_invalid = plmn_container["rsrp_stat"]["INVALID_VALUE"]
            p_rsrp_counter = int(100 * n_rsrp_invalid / meas_frame_counter)
            actual_result = f"#RSRP_INVALID = {p_rsrp_counter}% ({n_rsrp_invalid}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrp_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # RSRQ Check
            # Step: Check RSRQ EXCELLENT or GOOD occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRQ_EXCELLENT_OR_GOOD"
            expected_result = "#RSRQ_EXCELLENT_OR_GOOD > 80%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrq_excellent_or_good = plmn_container["rsrq_stat"]["excellent"] + plmn_container["rsrq_stat"]["good"]
            p_rsrq_counter = int(100 * n_rsrq_excellent_or_good / meas_frame_counter)
            actual_result = f"#RSRQ_EXCELLENT_OR_GOOD = {p_rsrq_counter}% ({n_rsrq_excellent_or_good}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrq_counter > 80 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRQ RSRQ_FAIR_TO_POOR occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRQ_FAIR_TO_POOR"
            expected_result = "#RSRQ_FAIR_TO_POOR < 50%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrq_fair_to_poor = plmn_container["rsrq_stat"]["fair_to_poor"]
            p_rsrq_counter = int(100 * n_rsrq_fair_to_poor / meas_frame_counter)
            actual_result = f"#RSRQ_FAIR_TO_POOR = {p_rsrq_counter}% ({n_rsrq_fair_to_poor}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrq_counter < 50 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRQ POOR occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRQ_POOR"
            expected_result = "#RSRQ_POOR < 20%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrq_poor = plmn_container["rsrq_stat"]["poor"]
            p_rsrq_counter = int(100 * n_rsrq_poor / meas_frame_counter)
            actual_result = f"#RSRQ_POOR = {p_rsrq_counter}% ({n_rsrq_poor}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrq_counter < 20 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRQ RSRQ 255 occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRQ_255"
            expected_result = "#RSRQ_255 < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrq_255 = plmn_container["rsrq_stat"]["error_255"]
            p_rsrq_counter = int(100 * n_rsrq_255 / meas_frame_counter)
            actual_result = f"#RSRQ_255 = {p_rsrq_counter}% ({n_rsrq_255}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrq_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check RSRQ INVALID occurrances
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #RSRQ_INVALID"
            expected_result = "#RSRQ_INVALID < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_rsrq_invalid = plmn_container["rsrq_stat"]["INVALID_VALUE"]
            p_rsrq_counter = int(100 * n_rsrq_invalid / meas_frame_counter)
            actual_result = f"#RSRQ_INVALID = {p_rsrq_counter}% ({n_rsrq_invalid}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_rsrq_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # TX POWER Check
            # Step: Check TX Power cat 1
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #TX_PWR_CAT1"
            expected_result = "#TX_PWR_CAT1 > 80%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_tx_pwr_cat_1 = plmn_container["tx_pwr_stat"]["cat_1"]
            p_tx_pwr_counter = int(100 * n_tx_pwr_cat_1 / meas_frame_counter)
            actual_result = f"#TX_PWR_CAT1 = {p_tx_pwr_counter}% ({n_tx_pwr_cat_1}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_tx_pwr_counter > 80 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check TX Power cat 2
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #TX_PWR_CAT2"
            expected_result = "#TX_PWR_CAT2 < 50%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_tx_pwr_cat_2 = plmn_container["tx_pwr_stat"]["cat_2"]
            p_tx_pwr_counter = int(100 * n_tx_pwr_cat_2 / meas_frame_counter)
            actual_result = f"#TX_PWR_CAT2 = {p_tx_pwr_counter}% ({n_tx_pwr_cat_2}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_tx_pwr_counter < 50 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check TX Power 255
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #TX_PWR_255"
            expected_result = "#TX_PWR_255 < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_tx_pwr_255 = plmn_container["tx_pwr_stat"]["error_255"]
            p_tx_pwr_counter = int(100 * n_tx_pwr_255 / meas_frame_counter)
            actual_result = f"#TX_PWR_255 = {p_tx_pwr_counter}% ({n_tx_pwr_255}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_tx_pwr_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)

            # Step: Check TX Power INVALID
            current_test_step += 1
            step_description = f"{meas_plmn}: Check #TX_PWR_INVALID"
            expected_result = "#TX_PWR_INVALID < 10%"
            self.logger.info("Step {meas_plmn}: {step_description}")
            n_tx_pwr_inv = plmn_container["tx_pwr_stat"]["INVALID_VALUE"]
            p_tx_pwr_counter = int(100 * n_tx_pwr_inv / meas_frame_counter)
            actual_result = f"#TX_PWR_INVALID = {p_tx_pwr_counter}% ({n_tx_pwr_inv}/{meas_frame_counter})"
            step_verdict = self.result_classifier.PASSED if p_tx_pwr_counter < 10 else self.result_classifier.FAILED
            self.save_step(current_test_step, step_description, expected_result, actual_result, step_verdict)
