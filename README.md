# GPU Passthrough Setup for Proxmox

This project provides a script to facilitate GPU passthrough setup on Proxmox hosts. 
It automates the configuration process, ensuring that your Proxmox environment is ready
to utilize GPUs within virtual machines.

## Features

- **Automated Configuration**: Simplifies the setup process for GPU passthrough on Proxmox hosts.
- **Dry Run Option**: Allows you to simulate changes before applying them, ensuring safety and predictability.
- **Comprehensive Logging**: Detailed logging for tracking the configuration process and troubleshooting potential issues.

## Requirements

- A Proxmox host with GPU hardware.
- Python 3.6 or higher.

## Installation

Clone the repository to your local machine:

```bash
git clone https://github.com/pedroanisio/gpu-passthrough-setup.git
cd gpu-passthrough-setup
```

## Usage

To execute the script:

```bash
./main.py
```

To perform a dry run:

```bash
./main.py --dry-run
```

## Configuration Files

- `config/settings.json`: Contains the settings for preconditions and desired state checks.

## Modules

### Bootloader Module

Handles the determination of the bootloader type (e.g., GRUB in BIOS/Legacy mode, GRUB in UEFI mode, systemd-boot).

### CommandExecutor Module

Executes shell commands and handles errors, ensuring commands are run correctly and logs the output.

### GrubConfig Module

Backs up and modifies the GRUB configuration to include necessary settings for IOMMU.

### HardwareInfo Module

Logs and retrieves detailed hardware information including CPU, motherboard, and GPU details.

### SystemPreconditions Module

Checks and verifies system preconditions against the settings in the configuration file.

### SystemConfigurator Module

Coordinates the configuration process, prepares commands based on discrepancies, and applies the necessary changes.

### VFIO Module

Ensures VFIO modules are loaded and creates configuration files to specify PCI IDs for GPU isolation.

### Logger Module

Sets up logging to both console and file for tracking the configuration process and troubleshooting.

## Logging

Logs are created in the `logs/` directory with detailed information about each step of the configuration process.

## Troubleshooting

If you encounter any issues, refer to the logs in the `logs/` directory for detailed error messages and steps taken during the configuration process.

## Contribution

Feel free to fork the repository and submit pull requests. Contributions are welcome!

## Inspiration

This script was inspired by the [PCI GPU Passthrough on Proxmox VE 8: Installation and Configuration](https://forum.proxmox.com/threads/pci-gpu-passthrough-on-proxmox-ve-8-installation-and-configuration.130218/) thread on the Proxmox forum.

## Settings Configuration

The `settings.json` file is crucial for defining the preconditions and desired states the script needs to check and enforce. Below is a detailed explanation of the structure and purpose of each section within the `settings.json` file:

### Preconditions

The preconditions section ensures that the script is run in an appropriate environment and checks for basic requirements. It contains an array of command objects, each with the following fields:

- **description**: A brief description of what the precondition is checking.
- **command**: The shell command that is executed to check the precondition.
- **expected_output**: The exact expected output of the command.
- **expected_output_contains**: A substring that should be present in the command's output (optional).
- **failure_message**: The message that will be logged if the precondition is not met.

#### Preconditions Settings

```json
{
    "preconditions": {
        "commands": [
            {
                "description": "Check if script is run as root",
                "command": "id -u",
                "expected_output": "0",
                "failure_message": "Script must be run as root."
            },
            {
                "description": "Check if Proxmox host",
                "command": "test -d /etc/pve && echo exists",
                "expected_output": "exists",
                "failure_message": "This script must be run on a Proxmox host."
            },
            {
                "description": "Check if GPU exists",
                "command": "lspci | grep -i vga",
                "expected_output_contains": "VGA",
                "failure_message": "No GPU found. GPU is mandatory."
            }
        ]
    }
}
```

1. **Check if script is run as root**:
    - **Command**: `id -u`
    - **Expected Output**: `0`
    - **Reason**: Ensures the script has the necessary permissions to make system-level changes.

2. **Check if Proxmox host**:
    - **Command**: `test -d /etc/pve && echo exists`
    - **Expected Output**: `exists`
    - **Reason**: Confirms that the script is running on a Proxmox host, which is required for the passthrough setup.

3. **Check if GPU exists**:
    - **Command**: `lspci | grep -i vga`
    - **Expected Output Contains**: `VGA`
    - **Reason**: Verifies that a GPU is present on the host, as GPU passthrough cannot be configured without a GPU.

### Desired State

The desired state section defines the checks and configurations that need to be applied to ensure the system is set up correctly for GPU passthrough. It also contains an array of command objects, each with the following fields:

- **description**: A brief description of what the desired state check or configuration is ensuring.
- **command**: The shell command that is executed to check or enforce the desired state.
- **expected_output**: The exact expected output of the command (optional).
- **expected_output_contains**: A substring that should be present in the command's output.
- **optional_expected_output_contains**: Additional substrings that are acceptable in the command's output (optional).
- **failure_message**: The message that will be logged if the desired state is not met.

#### Desired State Settings

```json
{
    "desired_state": {
        "commands": [
            {
                "description": "Check if CPU model is AMD or Intel",
                "command": "lscpu | grep 'Model name'",
                "expected_output_contains": "AMD",
                "failure_message": "CPU model is not AMD or Intel.",
                "optional_expected_output_contains": ["Intel"]
            },
            {
                "description": "Check if GPU type is NVIDIA, AMD, or Intel",
                "command": "lspci | grep -i 'vga\\|3d'",
                "expected_output_contains": "NVIDIA",
                "failure_message": "GPU type is not NVIDIA, AMD, or Intel.",
                "optional_expected_output_contains": ["AMD", "Intel"]
            },
            {
                "description": "Check if IOMMU is enabled",
                "command": "dmesg | grep -e IOMMU",
                "expected_output_contains": "IOMMU",
                "failure_message": "IOMMU is not enabled."
            },
            {
                "description": "Check if VFIO modules are loaded",
                "command": "lsmod | grep vfio",
                "expected_output_contains": "vfio",
                "failure_message": "VFIO modules are not loaded."
            },
            {
                "description": "Check if GRUB has IOMMU settings",
                "command": "grep 'iommu=pt' /etc/default/grub",
                "expected_output_contains": "iommu=pt",
                "failure_message": "GRUB is not configured with IOMMU settings."
            },
            {
                "description": "Check if kvm.conf has Nvidia Card settings",
                "command": "grep 'options kvm ignore_msrs=1 report_ignored_msrs=0' /etc/modprobe.d/kvm.conf",
                "expected_output_contains": "options kvm ignore_msrs=1 report_ignored_msrs=0",
                "failure_message": "Nvidia Card settings not found in kvm.conf."
            },
            {
                "description": "Check if AMD drivers are blacklisted",
                "command": "grep 'blacklist radeon' /etc/modprobe.d/blacklist.conf && grep 'blacklist amdgpu' /etc/modprobe.d/blacklist.conf",
                "expected_output_contains": "blacklist radeon",
                "failure_message": "AMD drivers are not blacklisted."
            },
            {
                "description": "Check if NVIDIA drivers are blacklisted",
                "command": "grep 'blacklist nouveau' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidia' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidiafb' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidia_drm' /etc/modprobe.d/blacklist.conf",
                "expected_output_contains": "blacklist nouveau",
                "failure_message": "NVIDIA drivers are not blacklisted."
            },
            {
                "description": "Check if Intel drivers are blacklisted",
                "command": "grep 'blacklist snd_hda_intel' /etc/modprobe.d/blacklist.conf && grep 'blacklist snd_hda_codec_hdmi' /etc/modprobe.d/blacklist.conf && grep 'blacklist i915' /etc/modprobe.d/blacklist.conf",
                "expected_output_contains": "blacklist snd_hda_intel",
                "failure_message": "Intel drivers are not blacklisted."
            }
        ]
    }
}
```

1. **Check if CPU model is AMD or Intel**:
    - **Command**: `lscpu | grep 'Model name'`
    - **Expected Output Contains**: `AMD`
    - **Optional Expected Output Contains**: `Intel`
    - **Reason**: Ensures the CPU model is either AMD or Intel, as the script currently supports these two CPU types for GPU passthrough.

2. **Check if GPU type is NVIDIA, AMD, or Intel**:
    - **Command**: `lspci | grep -i 'vga\\|3d'`
    - **Expected Output Contains**: `NVIDIA`
    - **Optional Expected Output Contains**: `AMD`, `Intel`
    - **Reason**: Confirms the GPU type, as the script supports these GPU vendors for passthrough configuration.

3. **Check if IOMMU is enabled**:
    - **Command**: `dmesg | grep -e IOMMU`
    - **Expected Output Contains**: `IOMMU`
    - **Reason**: Verifies that IOMMU (Input-Output Memory Management Unit) is enabled, which is necessary for GPU passthrough.

4. **Check if VFIO modules are loaded**:
    - **Command**: `lsmod | grep vfio`
    - **Expected Output Contains**: `vfio`
    - **Reason**: Ensures that the VFIO (Virtual Function I/O) modules are loaded, which are required for binding GPUs to virtual machines.

5. **Check if GRUB has IOMMU settings**:
    - **Command**: `grep 'iommu=pt' /etc/default/grub`
    - **Expected Output Contains**: `iommu=pt`
    - **Reason**: Confirms that the GRUB bootloader is configured with IOMMU settings, which are necessary for enabling IOMMU on boot.

6. **Check if kvm.conf has Nvidia Card settings**:
    - **Command**: `grep 'options kvm ignore_msrs=1 report_ignored_msrs=0' /etc/modprobe.d/kvm.conf`
    - **Expected Output Contains**: `options kvm ignore_msrs=1 report_ignored_msrs=0`
    - **Reason**: Ensures that the KVM (Kernel-based Virtual Machine) configuration file has settings specific to Nvidia GPUs, necessary for proper GPU passthrough.

7. **Check if AMD drivers are blacklisted**:
    - **Command**: `grep 'blacklist radeon' /etc/modprobe.d/blacklist.conf && grep 'blacklist amdgpu' /etc/modprobe.d/blacklist.conf`
    - **Expected Output Contains**: `blacklist radeon`
    - **Reason**: Ensures that AMD drivers are blacklisted

 to avoid conflicts with the GPU passthrough setup.

8. **Check if NVIDIA drivers are blacklisted**:
    - **Command**: `grep 'blacklist nouveau' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidia' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidiafb' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidia_drm' /etc/modprobe.d/blacklist.conf`
    - **Expected Output Contains**: `blacklist nouveau`
    - **Reason**: Ensures that NVIDIA drivers are blacklisted to avoid conflicts with the GPU passthrough setup.

9. **Check if Intel drivers are blacklisted**:
    - **Command**: `grep 'blacklist snd_hda_intel' /etc/modprobe.d/blacklist.conf && grep 'blacklist snd_hda_codec_hdmi' /etc/modprobe.d/blacklist.conf && grep 'blacklist i915' /etc/modprobe.d/blacklist.conf`
    - **Expected Output Contains**: `blacklist snd_hda_intel`
    - **Reason**: Ensures that Intel drivers are blacklisted to avoid conflicts with the GPU passthrough setup.

### Example `settings.json` File

```json
{
    "preconditions": {
        "commands": [
            {
                "description": "Check if script is run as root",
                "command": "id -u",
                "expected_output": "0",
                "failure_message": "Script must be run as root."
            },
            {
                "description": "Check if Proxmox host",
                "command": "test -d /etc/pve && echo exists",
                "expected_output": "exists",
                "failure_message": "This script must be run on a Proxmox host."
            },
            {
                "description": "Check if GPU exists",
                "command": "lspci | grep -i vga",
                "expected_output_contains": "VGA",
                "failure_message": "No GPU found. GPU is mandatory."
            }
        ]
    },
    "desired_state": {
        "commands": [
            {
                "description": "Check if CPU model is AMD or Intel",
                "command": "lscpu | grep 'Model name'",
                "expected_output_contains": "AMD",
                "failure_message": "CPU model is not AMD or Intel.",
                "optional_expected_output_contains": ["Intel"]
            },
            {
                "description": "Check if GPU type is NVIDIA, AMD, or Intel",
                "command": "lspci | grep -i 'vga\\|3d'",
                "expected_output_contains": "NVIDIA",
                "failure_message": "GPU type is not NVIDIA, AMD, or Intel.",
                "optional_expected_output_contains": ["AMD", "Intel"]
            },
            {
                "description": "Check if IOMMU is enabled",
                "command": "dmesg | grep -e IOMMU",
                "expected_output_contains": "IOMMU",
                "failure_message": "IOMMU is not enabled."
            },
            {
                "description": "Check if VFIO modules are loaded",
                "command": "lsmod | grep vfio",
                "expected_output_contains": "vfio",
                "failure_message": "VFIO modules are not loaded."
            },
            {
                "description": "Check if GRUB has IOMMU settings",
                "command": "grep 'iommu=pt' /etc/default/grub",
                "expected_output_contains": "iommu=pt",
                "failure_message": "GRUB is not configured with IOMMU settings."
            },
            {
                "description": "Check if kvm.conf has Nvidia Card settings",
                "command": "grep 'options kvm ignore_msrs=1 report_ignored_msrs=0' /etc/modprobe.d/kvm.conf",
                "expected_output_contains": "options kvm ignore_msrs=1 report_ignored_msrs=0",
                "failure_message": "Nvidia Card settings not found in kvm.conf."
            },
            {
                "description": "Check if AMD drivers are blacklisted",
                "command": "grep 'blacklist radeon' /etc/modprobe.d/blacklist.conf && grep 'blacklist amdgpu' /etc/modprobe.d/blacklist.conf",
                "expected_output_contains": "blacklist radeon",
                "failure_message": "AMD drivers are not blacklisted."
            },
            {
                "description": "Check if NVIDIA drivers are blacklisted",
                "command": "grep 'blacklist nouveau' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidia' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidiafb' /etc/modprobe.d/blacklist.conf && grep 'blacklist nvidia_drm' /etc/modprobe.d/blacklist.conf",
                "expected_output_contains": "blacklist nouveau",
                "failure_message": "NVIDIA drivers are not blacklisted."
            },
            {
                "description": "Check if Intel drivers are blacklisted",
                "command": "grep 'blacklist snd_hda_intel' /etc/modprobe.d/blacklist.conf && grep 'blacklist snd_hda_codec_hdmi' /etc/modprobe.d/blacklist.conf && grep 'blacklist i915' /etc/modprobe.d/blacklist.conf",
                "expected_output_contains": "blacklist snd_hda_intel",
                "failure_message": "Intel drivers are not blacklisted."
            }
        ]
    }
}
```