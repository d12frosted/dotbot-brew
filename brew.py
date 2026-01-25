import os
import shutil
import subprocess
import sys

import dotbot

class Brew(dotbot.Plugin):
    _brewDirective = "brew"
    _caskDirective = "cask"
    _tapDirective = "tap"
    _brewFileDirective = "brewfile"
    _servicesDirective = "services"

    def __init__(self, context):
        super(Brew, self).__init__(context)
        self._brew_path = None

    def can_handle(self, directive):
        return directive in (self._tapDirective, self._brewDirective, self._caskDirective, self._brewFileDirective, self._servicesDirective)

    def handle(self, directive, data):
        if directive == self._tapDirective:
            self._bootstrap_brew()
            return self._tap(data)
        if directive == self._brewDirective:
            self._bootstrap_brew()
            return self._process_data(f"{self._brew_path} install", data)
        if directive == self._caskDirective:
            if sys.platform.startswith("darwin"):
                self._bootstrap_brew()
                return self._process_data(f"{self._brew_path} install --cask", data)
            else:
                self._log.warning('Cask directive is only supported on macOS, skipping')
                return True
        if directive == self._brewFileDirective:
            self._bootstrap_brew()
            return self._install_bundle(data)
        if directive == self._servicesDirective:
            self._bootstrap_brew()
            return self._start_services(data)
        raise ValueError(f'Brew cannot handle directive {directive}')

    def _tap(self, tap_list):
        cwd = self._context.base_directory()
        for tap in tap_list:
            self._log.info(f"Tapping {tap}")
            cmd = f"{self._brew_path} tap {tap}"
            result = subprocess.call(cmd, shell=True, cwd=cwd)
            if result != 0:
                self._log.warning(f'Failed to tap [{tap}]')
                return False
        return True

    def _process_data(self, install_cmd, data):
        success = self._install(install_cmd, data)
        if success:
            self._log.info('All packages have been installed')
        else:
            self._log.error('Some packages were not installed')
        return success

    def _install(self, install_cmd, packages_list):
        cwd = self._context.base_directory()
        for package in packages_list:
            if "--cask" in install_cmd:
                check_cmd = f"{self._brew_path} list --cask --versions {package}"
            else:
                check_cmd = f"{self._brew_path} list --versions {package}"
            already_installed = subprocess.call(
                check_cmd, shell=True, cwd=cwd,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ) == 0
            if not already_installed:
                self._log.info(f"Installing {package}")
                cmd = f"{install_cmd} {package}"
                result = subprocess.call(cmd, shell=True, cwd=cwd)
                if result != 0:
                    self._log.warning(f'Failed to install [{package}]')
                    return False
        return True

    def _install_bundle(self, brew_files):
        cwd = self._context.base_directory()
        for f in brew_files:
            self._log.info(f"Installing from file {f}")
            cmd = f"{self._brew_path} bundle --verbose --file={f}"
            result = subprocess.call(cmd, shell=True, cwd=cwd)
            if result != 0:
                self._log.warning(f'Failed to install file [{f}]')
                return False
        return True

    def _start_services(self, services_list):
        cwd = self._context.base_directory()
        for service in services_list:
            self._log.info(f"Starting service {service}")
            cmd = f"{self._brew_path} services start {service}"
            result = subprocess.call(cmd, shell=True, cwd=cwd)
            if result != 0:
                self._log.warning(f'Failed to start service [{service}]')
                return False
        self._log.info('All services have been started')
        return True

    def _get_brew_path(self):
        """Standard Homebrew installation locations across OS and Architectures."""
        locations = [
            "/opt/homebrew/bin/brew",          # Apple Silicon macOS
            "/usr/local/bin/brew",             # Intel macOS
            "/home/linuxbrew/.linuxbrew/bin/brew" # Linux
        ]
        
        # Check current PATH first
        system_brew = shutil.which("brew")
        if system_brew:
            return system_brew
            
        # Check standard installation directories
        for loc in locations:
            if os.path.exists(loc) and os.access(loc, os.X_OK):
                return loc
        return None

    def _bootstrap_brew(self):
        """Installs Homebrew if missing and updates the internal _brew_path."""
        self._brew_path = self._get_brew_path()
        
        if self._brew_path:
            self._log.debug(f"Using Homebrew found at: {self._brew_path}")
            subprocess.call(f"{self._brew_path} update-if-needed", shell=True, 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            self._log.info("Homebrew not found. Installing...")
            link = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
            # We use /bin/bash explicitly as the installer requires it
            cmd = f'NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL {link})"'
            subprocess.call(cmd, shell=True, cwd=self._context.base_directory(),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # Resolve path again after installation
            self._brew_path = self._get_brew_path()
            
            if self._brew_path:
                self._log.info(f"Homebrew successfully installed at {self._brew_path}")
            else:
                self._log.error("Homebrew installation failed or path not found.")

