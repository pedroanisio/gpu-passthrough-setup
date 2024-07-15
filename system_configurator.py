import subprocess
from command_executor import CommandExecutor
from logger import logger
from hardware_info import HardwareInfo
from bootloader import Bootloader
from grub_config import GrubConfig
from vfio import VFIO
from preconditions import SystemPreconditions
from configuration_error import ConfigurationError

class SystemConfigurator:
    def __init__(self, dry_run=False):
        self.commands = []
        self.rollback_commands = []
        self.preconditions = SystemPreconditions()
        self.dry_run = dry_run

    def configure_system(self):
        """Configures the system for GPU passthrough."""
        try:
            hardware_info, unmet_preconditions = self.preconditions.check()
            gpu_type = hardware_info['gpu']['type']
            if unmet_preconditions:
                if "Check if GRUB has IOMMU settings" in unmet_preconditions:
                    grub_config = GrubConfig()
                    grub_config.backup_grub_config()
                    self.commands.append(grub_config.modify_grub_config())
                    self.rollback_commands.append(grub_config.restore_grub_config())
                if "Check if VFIO modules are loaded" in unmet_preconditions:
                    VFIO.ensure_vfio_modules()
                if "Check if kvm.conf has Nvidia Card settings" in unmet_preconditions and gpu_type == 'nvidia':
                    vfio_conf_command = self.create_vfio_conf(hardware_info['gpu']['codes'])
                    self.commands.append(vfio_conf_command)
                    self.rollback_commands.append("rm /etc/modprobe.d/vfio.conf")
                if "Check if AMD drivers are blacklisted" in unmet_preconditions and gpu_type == 'amd':
                    blacklist_command = self.blacklist_drivers('amd')
                    self.commands.append(blacklist_command)
                    self.rollback_commands.append(self.unblacklist_drivers('amd'))
                if "Check if NVIDIA drivers are blacklisted" in unmet_preconditions and gpu_type == 'nvidia':
                    blacklist_command = self.blacklist_drivers('nvidia')
                    self.commands.append(blacklist_command)
                    self.rollback_commands.append(self.unblacklist_drivers('nvidia'))
                if "Check if Intel drivers are blacklisted" in unmet_preconditions and gpu_type == 'intel':
                    blacklist_command = self.blacklist_drivers('intel')
                    self.commands.append(blacklist_command)
                    self.rollback_commands.append(self.unblacklist_drivers('intel'))
                
                bootloader = Bootloader.determine_bootloader()
                self.commands.extend(self.get_bootloader_specific_commands(bootloader))
                
                if self.dry_run:
                    self.dry_run_commands()
                else:
                    for command in self.commands:
                        CommandExecutor.execute(command)
                
                logger.info("System configured successfully.")
                self.check_iommu_enabled()
                discrepancies = self.preconditions.compare_states()
                if discrepancies:
                    logger.warning("There are discrepancies between the actual and desired states. Please review.")
            else:
                logger.info("All preconditions are already met. No configuration needed.")
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

    def create_vfio_conf(self, pci_ids):
        """Creates a configuration file for VFIO to specify PCI IDs to be isolated."""
        vfio_conf = f"options vfio-pci ids={','.join(pci_ids)}"
        return f"echo \"{vfio_conf}\" > /etc/modprobe.d/vfio.conf"

    def blacklist_drivers(self, gpu_type):
        """Blacklists drivers to avoid conflicts with the Proxmox host."""
        blacklist_commands = []
        if gpu_type == 'amd':
            blacklist_commands.extend([
                "echo \"blacklist radeon\" >> /etc/modprobe.d/blacklist.conf",
                "echo \"blacklist amdgpu\" >> /etc/modprobe.d/blacklist.conf"
            ])
        elif gpu_type == 'nvidia':
            blacklist_commands.extend([
                "echo \"blacklist nouveau\" >> /etc/modprobe.d/blacklist.conf",
                "echo \"blacklist nvidia\" >> /etc/modprobe.d/blacklist.conf",
                "echo \"blacklist nvidiafb\" >> /etc/modprobe.d/blacklist.conf",
                "echo \"blacklist nvidia_drm\" >> /etc/modprobe.d/blacklist.conf"
            ])
        elif gpu_type == 'intel':
            blacklist_commands.extend([
                "echo \"blacklist snd_hda_intel\" >> /etc/modprobe.d/blacklist.conf",
                "echo \"blacklist snd_hda_codec_hdmi\" >> /etc/modprobe.d/blacklist.conf",
                "echo \"blacklist i915\" >> /etc/modprobe.d/blacklist.conf"
            ])
        return " && ".join(blacklist_commands)

    def unblacklist_drivers(self, gpu_type):
        """Removes driver blacklists."""
        unblacklist_commands = []
        if gpu_type == 'amd':
            unblacklist_commands.extend([
                "sed -i '/blacklist radeon/d' /etc/modprobe.d/blacklist.conf",
                "sed -i '/blacklist amdgpu/d' /etc/modprobe.d/blacklist.conf"
            ])
        elif gpu_type == 'nvidia':
            unblacklist_commands.extend([
                "sed -i '/blacklist nouveau/d' /etc/modprobe.d/blacklist.conf",
                "sed -i '/blacklist nvidia/d' /etc/modprobe.d/blacklist.conf",
                "sed -i '/blacklist nvidiafb/d' /etc/modprobe.d/blacklist.conf",
                "sed -i '/blacklist nvidia_drm/d' /etc/modprobe.d/blacklist.conf"
            ])
        elif gpu_type == 'intel':
            unblacklist_commands.extend([
                "sed -i '/blacklist snd_hda_intel/d' /etc/modprobe.d/blacklist.conf",
                "sed -i '/blacklist snd_hda_codec_hdmi/d' /etc/modprobe.d/blacklist.conf",
                "sed -i '/blacklist i915/d' /etc/modprobe.d/blacklist.conf"
            ])
        return " && ".join(unblacklist_commands)

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

    def dry_run_commands(self):
        """Logs the commands that would be executed during a dry run."""
        logger.info("Dry run: the following commands would be executed:")
        for command in self.commands:
            logger.info(f"Command: {command}")
        logger.info("Dry run complete: no changes have been made.")
