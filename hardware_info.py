import subprocess
from logger import logger
from preconditions import ConfigurationError

class HardwareInfo:
    def __init__(self):
        self.hardware_info = {
            'cpu': {'model': None, 'detail': None},
            'motherboard': {'model': None, 'detail': None},
            'gpu': {'exists': False, 'model': None, 'detail': None, 'type': None}
        }

    def log_hardware_info(self):
        """Logs and retrieves hardware information."""
        logger.info("Logging hardware information...")
        
        try:
            motherboard_info = subprocess.check_output("sudo dmidecode -t baseboard", shell=True).decode()
            cpu_info = subprocess.check_output("lscpu", shell=True).decode()
            gpu_info = subprocess.check_output("lspci | grep -i vga", shell=True).decode()

            self._parse_motherboard_info(motherboard_info)
            self._parse_cpu_info(cpu_info)
            self._parse_gpu_info(gpu_info)

            logger.info(f"Motherboard Info:\n{motherboard_info}")
            logger.info(f"CPU Info:\n{cpu_info}")
            logger.info(f"GPU Info:\n{gpu_info}")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to retrieve hardware information: {e.stderr.decode()}")
            raise ConfigurationError("Hardware information retrieval failed.")

        return self.hardware_info

    def _parse_motherboard_info(self, info):
        """Parses motherboard information."""
        for line in info.split('\n'):
            if "Product Name:" in line:
                self.hardware_info['motherboard']['model'] = line.split(":")[1].strip()
                break
        self.hardware_info['motherboard']['detail'] = info

    def _parse_cpu_info(self, info):
        """Parses CPU information."""
        for line in info.split('\n'):
            if "Model name:" in line:
                self.hardware_info['cpu']['model'] = line.split(":")[1].strip()
                break
        self.hardware_info['cpu']['detail'] = info

    def _parse_gpu_info(self, info):
        """Parses GPU information."""
        if info:
            self.hardware_info['gpu']['exists'] = True
            self.hardware_info['gpu']['model'] = info.split(":")[2].strip()
            self.hardware_info['gpu']['detail'] = info
            if "intel" in info.lower():
                self.hardware_info['gpu']['type'] = 'intel'
            elif "amd" in info.lower() or "advanced micro devices" in info.lower():
                self.hardware_info['gpu']['type'] = 'amd'
            elif "nvidia" in info.lower():
                self.hardware_info['gpu']['type'] = 'nvidia'
            else:
                raise ConfigurationError("Unknown GPU type detected.")
