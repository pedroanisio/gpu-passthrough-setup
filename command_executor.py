import subprocess
from logger import logger

class CommandExecutor:
    @staticmethod
    def execute(command):
        """Executes a shell command."""
        logger.info(f"Executing: {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr.decode()}")
            raise

    @staticmethod
    def rollback(command):
        """Rolls back a shell command."""
        logger.info(f"Rolling back: {command}")
        try:
            result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.info(result.stdout.decode())
        except subprocess.CalledProcessError as e:
            logger.error(f"Rollback failed: {e.stderr.decode()}")
