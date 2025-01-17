import subprocess
import json
import os
from src.command_executor import CommandExecutor
from src.logger import logger
from src.grub_config import GrubConfig
from src.vfio import VFIO
from src.preconditions import SystemPreconditions
from src.configuration_error import ConfigurationError

class SystemConfigurator:
    def __init__(self, dry_run=False, settings_file='config/settings.json'):
        self.commands = []
        self.rollback_commands = []
        self.preconditions = SystemPreconditions(settings_file)
        self.dry_run = dry_run
        self.settings = self.load_settings(settings_file)

    @staticmethod
    def load_settings(settings_file):
        """Loads settings from a JSON file."""
        with open(settings_file, 'r') as f:
            return json.load(f)

    def configure_system(self):
        """Configures the system for GPU passthrough."""
        try:
            hardware_info, unmet_preconditions = self.preconditions.check()
            gpu_type = hardware_info['gpu']['type']

            if not unmet_preconditions:
                discrepancies = self.preconditions.compare_states()            
                self.prepare_commands(discrepancies, hardware_info)
                self.update_ramfs()  # Add this line to update ramfs    
                                
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
                logger.warning("Some preconditions were not met. Please resolve the issues and try again.")
        except Exception as e:
            logger.error(f"An error occurred: {e}. Rolling back changes...")
            for command in self.rollback_commands:
                CommandExecutor.rollback(command)
            logger.error("Rollback complete. Please check the system state.")
            raise

    def prepare_commands(self, discrepancies, hardware_info):
        """Prepares the necessary commands based on discrepancies."""
        gpu_type = hardware_info['gpu']['type']
        for condition in self.settings['desired_state']['commands']:
            description = condition['description']

            if description in discrepancies:
                if "GRUB has IOMMU settings" in description:
                    grub_config = GrubConfig()
                    grub_config.backup_grub_config()
                    self.commands.append(grub_config.modify_grub_config())
                    self.rollback_commands.append(grub_config.restore_grub_config())
                elif "VFIO modules are loaded" in description:
                    VFIO.ensure_vfio_modules()
                elif "kvm.conf has Nvidia Card settings" in description and gpu_type == 'nvidia':
                    vfio_conf_command = self.create_vfio_conf(hardware_info['gpu']['codes'])
                    self.commands.append(vfio_conf_command)
                    self.rollback_commands.append("rm /etc/modprobe.d/vfio.conf")
                elif "AMD drivers are blacklisted" in description and gpu_type == 'amd':
                    blacklist_command = self.blacklist_drivers('amd')
                    self.commands.append(blacklist_command)
                    self.rollback_commands.append(self.unblacklist_drivers('amd'))
                elif "NVIDIA drivers are blacklisted" in description and gpu_type == 'nvidia':
                    blacklist_command = self.blacklist_drivers('nvidia')
                    self.commands.append(blacklist_command)
                    self.rollback_commands.append(self.unblacklist_drivers('nvidia'))
                elif "Intel drivers are blacklisted" in description and gpu_type == 'intel':
                    blacklist_command = self.blacklist_drivers('intel')
                    self.commands.append(blacklist_command)
                    self.rollback_commands.append(self.unblacklist_drivers('intel'))

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

    def update_ramfs(self):
        logger.info("will update ramfs...")
        update_ramfs_command = "update-initramfs -u"
        self.commands.append(update_ramfs_command)

    def dry_run_commands(self):
        """Logs the commands that would be executed during a dry run."""
        logger.info("Dry run: the following commands would be executed:")
        for command in self.commands:
            logger.info(f"Command: {command}")
        logger.info("Dry run complete: no changes have been made.")
