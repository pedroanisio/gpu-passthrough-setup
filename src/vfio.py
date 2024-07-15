from src.logger import logger
from src.preconditions import ConfigurationError

class VFIO:
    @staticmethod
    def ensure_vfio_modules():
        """Ensures VFIO modules are loaded."""
        logger.info("Ensuring VFIO modules are loaded...")
        required_modules = ["vfio", "vfio_iommu_type1", "vfio_pci"]

        try:
            with open('/etc/modules', 'r') as f:
                modules = f.read().splitlines()

            with open('/etc/modules', 'a') as f:
                for module in required_modules:
                    if module not in modules:
                        f.write(f"{module}\n")
                        logger.info(f"Added {module} to /etc/modules.")
                    else:
                        logger.info(f"{module} is already present in /etc/modules.")
        except Exception as e:
            logger.error(f"Failed to ensure VFIO modules: {str(e)}")
            raise ConfigurationError("Failed to ensure VFIO modules.")
