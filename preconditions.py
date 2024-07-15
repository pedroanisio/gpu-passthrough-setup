import json
import subprocess
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
        self.check_command_preconditions(self.settings['preconditions']['commands'])
        
        hardware_info = HardwareInfo().log_hardware_info()
        self.actual_state['cpu_model'] = hardware_info['cpu']['model']
        self.actual_state['gpu_type'] = hardware_info['gpu']['type']
        self.actual_state['gpu_exists'] = hardware_info['gpu']['exists']
        
        logger.info("Preconditions met.")
        return hardware_info

    def check_command_preconditions(self, commands):
        """Checks command-based preconditions."""
        for condition in commands:
            description = condition['description']
            command = condition['command']
            expected_output = condition.get('expected_output')
            expected_output_contains = condition.get('expected_output_contains')
            failure_message = condition['failure_message']
            
            logger.info(f"Running precondition check: {description}")
            try:
                result = subprocess.check_output(command, shell=True, stderr=subprocess.PIPE).decode().strip()
                if expected_output and result != expected_output:
                    raise ConfigurationError(failure_message)
                if expected_output_contains and expected_output_contains not in result:
                    raise ConfigurationError(failure_message)
            except subprocess.CalledProcessError as e:
                stderr_output = e.stderr.decode().strip() if e.stderr else "No stderr output"
                logger.error(f"Precondition check failed: {stderr_output}")
                raise ConfigurationError(failure_message)

    def compare_states(self):
        """Compares actual state with desired state."""
        logger.info("Comparing actual state with desired state...")
        discrepancies = self.check_command_preconditions(self.settings['desired_state']['commands'])
        
        if discrepancies:
            logger.info("Discrepancies found between actual and desired states:")
            for key, value in discrepancies.items():
                logger.info(f"{key}: Desired = {value['desired']}, Actual = {value['actual']}")
        else:
            logger.info("System state matches the desired state.")
        
        return discrepancies

    def check_desired_state(self):
        """Checks if the system is in the desired state."""
        logger.info("Checking desired state...")
        return self.check_command_preconditions(self.settings['desired_state']['commands'])

# Function to check file existence and contents
def check_file_contents(file_path, search_string):
    if not os.path.exists(file_path):
        raise ConfigurationError(f"{file_path} does not exist.")
    try:
        with open(file_path, 'r') as file:
            contents = file.read()
            if search_string not in contents:
                raise ConfigurationError(f"{search_string} not found in {file_path}.")
    except Exception as e:
        logger.error(f"Failed to check file contents: {str(e)}")
        raise ConfigurationError(f"Failed to check contents of {file_path}.")
