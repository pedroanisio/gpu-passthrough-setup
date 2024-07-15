import shutil
import subprocess
from logger import logger
from preconditions import ConfigurationError

class GrubConfig:
    def __init__(self):
        self.backup_path = '/etc/default/grub.bak'
        self.grub_path = '/etc/default/grub'

    def backup_grub_config(self):
        """Backs up the GRUB configuration."""
        logger.info("Backing up /etc/default/grub")
        try:
            shutil.copy(self.grub_path, self.backup_path)
            logger.info("Backup created at /etc/default/grub.bak")
        except Exception as e:
            logger.error(f"Failed to backup /etc/default/grub: {str(e)}")
            raise ConfigurationError("Failed to backup /etc/default/grub")

    def modify_grub_config(self):
        """Modifies the GRUB configuration."""
        logger.info("Modifying /etc/default/grub")
        try:
            cpu_info = subprocess.check_output("lscpu", shell=True).decode().lower()
            if "amd" in cpu_info:
                required_settings = "quiet iommu=pt"
            elif "intel" in cpu_info:
                required_settings = "quiet intel_iommu=on iommu=pt"
            else:
                raise ConfigurationError("Unsupported CPU type. Only AMD and Intel CPUs are supported.")

            with open(self.grub_path, 'r') as f:
                grub_config = f.readlines()

            modified = False
            for i, line in enumerate(grub_config):
                if line.startswith('GRUB_CMDLINE_LINUX_DEFAULT'):
                    if required_settings not in line:
                        current_settings = line.split('=', 1)[1].strip().strip('"')
                        new_settings = f'GRUB_CMDLINE_LINUX_DEFAULT="{current_settings} {required_settings}"'
                        grub_config[i] = new_settings + '\n'
                        modified = True
                    break

            if not modified:
                logger.info("No modification needed for GRUB_CMDLINE_LINUX_DEFAULT.")
                return

            with open(self.grub_path, 'w') as f:
                f.writelines(grub_config)

            logger.info("Modified /etc/default/grub. Running update-grub.")
            self._execute_command("update-grub")
        except Exception as e:
            logger.error(f"Failed to modify /etc/default/grub: {str(e)}")
            raise ConfigurationError("Failed to modify /etc/default/grub")

    def _execute_command(self, command):
        """Executes a shell command."""
        logger.info(f"Executing: {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr.decode()}")
            raise ConfigurationError(f"Command execution failed: {command}")
