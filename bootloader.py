import subprocess
from logger import logger
from preconditions import ConfigurationError

class Bootloader:
    @staticmethod
    def determine_bootloader():
        """Determines the bootloader type."""
        logger.info("Determining bootloader...")
        try:
            efibootmgr_output = subprocess.check_output("efibootmgr -v", shell=True).decode()

            if "EFI variables are not supported" in efibootmgr_output:
                logger.info("GRUB is used in BIOS/Legacy mode.")
                return "grub-bios"

            if "proxmox" in efibootmgr_output.lower():
                if "grubx64.efi" in efibootmgr_output.lower():
                    logger.info("GRUB is used in UEFI mode.")
                    return "grub-uefi"
                elif "shimx64.efi" in efibootmgr_output.lower():
                    logger.info("GRUB with Secure Boot is used in UEFI mode.")
                    return "grub-uefi-secure"

            if "systemd-bootx64.efi" in efibootmgr_output.lower():
                logger.info("systemd-boot is used.")
                return "systemd-boot"

            raise ConfigurationError("Unable to determine bootloader type from efibootmgr output.")

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to determine bootloader: {e.stderr.decode()}")
            raise ConfigurationError
