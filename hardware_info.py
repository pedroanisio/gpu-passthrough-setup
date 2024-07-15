import subprocess
from logger import logger
from configuration_error import ConfigurationError

class HardwareInfo:
    def __init__(self):
        self.hardware_info = {
            'cpu': {'model': None, 'detail': None},
            'motherboard': {'model': None, 'detail': None},
            'gpu': {'exists': False, 'model': None, 'detail': None, 'type': None, 'codes': []}
        }

    def log_hardware_info(self):
        """Logs and retrieves hardware information."""
        logger.info("Logging hardware information...")

        try:
            motherboard_info = subprocess.check_output("sudo dmidecode -t baseboard", shell=True).decode()
            cpu_info = subprocess.check_output("lscpu", shell=True).decode()
            vga_info = subprocess.check_output("lspci -nn | grep -i vga", shell=True).decode()
            gpu_info = subprocess.check_output("lspci -nn", shell=True).decode()

            self._parse_motherboard_info(motherboard_info)
            self._parse_cpu_info(cpu_info)
            self._parse_gpu_info(vga_info, gpu_info)

            logger.info(f"Motherboard Info:\n{motherboard_info}")
            logger.info(f"CPU Info:\n{cpu_info}")
            logger.info(f"VGA Info:\n{vga_info}")
            logger.info(f"GPU Info:\n{gpu_info}")

        except subprocess.CalledProcessError as e:
            stderr_output = e.stderr.decode().strip() if e.stderr else "No stderr output"
            logger.error(f"Failed to retrieve hardware information: {stderr_output}")
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

    def _parse_gpu_info(self, vga_info, gpu_info):
        """Parses GPU information."""
        if vga_info:
            self.hardware_info['gpu']['exists'] = True
            self.hardware_info['gpu']['model'] = vga_info.split(":")[2].strip()
            self.hardware_info['gpu']['detail'] = vga_info
            gpu_type_detected = False

            if "intel" in vga_info.lower():
                self.hardware_info['gpu']['type'] = 'intel'
                gpu_type_detected = True
            elif "amd" in vga_info.lower() or "advanced micro devices" in vga_info.lower():
                self.hardware_info['gpu']['type'] = 'amd'
                gpu_type_detected = True
            elif "nvidia" in vga_info.lower():
                self.hardware_info['gpu']['type'] = 'nvidia'
                gpu_type_detected = True

            if not gpu_type_detected:
                raise ConfigurationError("Unknown GPU type detected.")
            
            # Extract GPU and associated audio device codes
            gpu_codes = []
            vga_bus_id = vga_info.split()[0].rsplit('.', 1)[0]  # Get the bus root (e.g., "0e:00")
            for line in gpu_info.split('\n'):
                if line and line.split()[0].rsplit('.', 1)[0] == vga_bus_id:
                    code = line.split('[')[-1].split(']')[0].strip()
                    gpu_codes.append(code)
            self.hardware_info['gpu']['codes'] = gpu_codes
