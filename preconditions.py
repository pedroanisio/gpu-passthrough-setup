import json
import subprocess
import os
from logger import logger
from hardware_info import HardwareInfo
from configuration_error import ConfigurationError

class SystemPreconditions:
    def __init__(self, settings_file='config/settings.json'):
        self.settings = self.load_settings(settings_file)
        self.actual_state = {}

    @staticmethod
    def load_settings(settings_file):
        """Loads settings from a JSON file."""
        with open(settings_file, 'r') as f:
            return json.load(f)

    def check(self):
        """Checks system preconditions."""
        logger.info("Checking preconditions...")
        unmet_preconditions = self.check_command_preconditions(self.settings['preconditions']['commands'])
        
        hardware_info = HardwareInfo().log_hardware_info()
        self.actual_state['cpu_model'] = hardware_info['cpu']['model']
        self.actual_state['gpu_type'] = hardware_info['gpu']['type']
        self.actual_state['gpu_exists'] = hardware_info['gpu']['exists']
        
        if unmet_preconditions:
            logger.warning("Some preconditions were not met.")
        else:
            logger.info("Preconditions met.")
        
        return hardware_info, unmet_preconditions

    def check_command_preconditions(self, commands):
        """Checks command-based preconditions."""
        unmet_preconditions = []
        for condition in commands:
            description = condition['description']
            command = condition['command']
            expected_output = condition.get('expected_output')
            expected_output_contains = condition.get('expected_output_contains')
            optional_expected_output_contains = condition.get('optional_expected_output_contains', [])
            failure_message = condition['failure_message']
            
            logger.info(f"Running precondition check: {description}")
            
            if "grep" in command and "modprobe.d" in command:
                file_path = command.split()[-1]
                if not os.path.isfile(file_path):
                    logger.error(f"Precondition check failed: {failure_message}")
                    unmet_preconditions.append(description)
                    continue

            try:
                result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE).decode().strip()
                if expected_output and result != expected_output:
                    logger.error(f"Precondition check failed: {failure_message}")
                    unmet_preconditions.append(description)
                if expected_output_contains and expected_output_contains not in result:
                    if not any(opt in result for opt in optional_expected_output_contains):
                        logger.error(f"Precondition check failed: {failure_message}")
                        unmet_preconditions.append(description)
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr.decode().strip() if e.stderr else "No stderr output"
                logger.error(f"Precondition check failed: {stderr_output}")
                unmet_preconditions.append(description)
        
        return unmet_preconditions

    def compare_states(self):
        """Compares actual state with desired state."""
        logger.info("Comparing actual state with desired state...")
        discrepancies = self.check_command_preconditions(self.settings['desired_state']['commands'])
        
        if discrepancies:
            logger.info("Discrepancies found between actual and desired states:")
            for discrepancy in discrepancies:
                logger.info(f"Discrepancy: {discrepancy}")
        else:
            logger.info("System state matches the desired state.")
        
        return discrepancies

    def check_desired_state(self):
        """Checks if the system is in the desired state."""
        logger.info("Checking desired state...")
        return self.check_command_preconditions(self.settings['desired_state']['commands'])
