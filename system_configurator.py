import subprocess
from command_executor import CommandExecutor
from logger import logger
from hardware_info import HardwareInfo
from bootloader import Bootloader
from grub_config import GrubConfig
from vfio import VFIO
from preconditions import SystemPreconditions, ConfigurationError

class SystemConfigurator:
    def __init__(self):
        self.commands = []
        self.rollback_commands = []
        self.preconditions = SystemPreconditions()

    def configure_system(self):
        """Configures the system for GPU passthrough."""
        try:
            hardware_info = self.preconditions.check()
            grub_config = GrubConfig()
            grub_config.backup_grub_config()
            grub_config.modify_grub_config()
            VFIO.ensure_vfio_modules()
            bootloader = Bootloader.determine_bootloader()
            
            self.commands.extend(self.get_bootloader_specific_commands(bootloader))
            
            for command in self.commands:
                CommandExecutor.execute(command)
            
            logger.info("System configured successfully.")
            self.check_iommu_enabled()
            discrepancies = self.preconditions.check_desired_state()
            if discrepancies:
                logger.warning("There are discrepancies between the actual and desired states. Please review.")
        except Exception as e:
            logger.error(f"An error occurred: {e}. Rolling back changes...")
            for command in self.rollback_commands:
                CommandExecutor.rollback(command)
            logger.error("Rollback complete. Please check the system state.")
            raise

    def get_bootloader_specific_commands(self, bootloader):
        """Returns bootloader specific commands."""
        if bootloader == "grub-bios":
            return self.get_grub_bios_commands()
        elif bootloader == "grub-uefi":
            return self.get_grub_uefi_commands()
        elif bootloader == "systemd-boot":
            return self.get_systemd_boot_commands()
        elif bootloader == "grub-uefi-secure":
            return self.get_grub_uefi_secure_commands()
        return []

    def get_grub_bios_commands(self):
        return [
            # Add specific commands for GRUB in BIOS/Legacy mode
        ]

    def get_grub_uefi_commands(self):
        return [
            # Add specific commands for GRUB in UEFI mode
        ]

    def get_grub_uefi_secure_commands(self):
        return [
            # Add specific commands for GRUB with Secure Boot in UEFI mode
        ]

    def get_systemd_boot_commands(self):
        return [
            # Add specific commands for systemd-boot
        ]

    def check_iommu_enabled(self):
        """Checks if IOMMU is enabled."""
        logger.info("Checking if IOMMU is enabled...")
        try:
            iommu_output = subprocess.check_output("dmesg | grep -e IOMMU", shell=True).decode()
            if "IOMMU" in iommu_output:
                logger.info("IOMMU is enabled.")
            else:
                logger.error("IOMMU is not enabled.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check IOMMU: {e.stderr.decode()}")
            raise ConfigurationError("Failed to check IOMMU.")
