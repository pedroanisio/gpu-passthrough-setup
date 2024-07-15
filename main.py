#!/usr/bin/env python3
# Author: ARC4D3 org
# Date: 2024-01-01
# Description: A script to setup Proxmox host to execute GPU passthrough

from src.system_configurator import SystemConfigurator
from src.preconditions import ConfigurationError
from src.logger import logger

def main():
    """Main function to run the GPU passthrough setup."""
    configurator = SystemConfigurator(dry_run=True)
    try:
        configurator.configure_system()
        logger.info("GPU passthrough setup completed successfully.")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
