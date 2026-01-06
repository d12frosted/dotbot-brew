import subprocess
import sys

import dotbot

class Brew(dotbot.Plugin):
    _brewDirective = "brew"
    _caskDirective = "cask"
    _tapDirective = "tap"
    _brewFileDirective = "brewfile"
    _servicesDirective = "services"

    def can_handle(self, directive):
        return directive in (self._tapDirective, self._brewDirective, self._caskDirective, self._brewFileDirective, self._servicesDirective)

    def handle(self, directive, data):
        if directive == self._tapDirective:
            self._bootstrap_brew()
            return self._tap(data)
        if directive == self._brewDirective:
            self._bootstrap_brew()
            return self._process_data("brew install", data)
        if directive == self._caskDirective:
            if sys.platform.startswith("darwin"):
                self._bootstrap_brew()
                return self._process_data("brew install --cask", data)
            else:
                self._log.warning('Cask directive is only supported on macOS, skipping')
                return True
        if directive == self._brewFileDirective:
            self._bootstrap_brew()
            return self._install_bundle(data)
        if directive == self._servicesDirective:
            self._bootstrap_brew()
            return self._start_services(data)
        raise ValueError('Brew cannot handle directive %s' % directive)

    def _tap(self, tap_list):
        cwd = self._context.base_directory()
        for tap in tap_list:
            self._log.info("Tapping %s" % tap)
            cmd = "brew tap %s" % tap
            result = subprocess.call(cmd, shell=True, cwd=cwd)
            if result != 0:
                self._log.warning('Failed to tap [%s]' % tap)
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
            if install_cmd == 'brew install':
                check_cmd = "brew list --versions %s" % package
            else:
                check_cmd = "brew list --cask --versions %s" % package
            already_installed = subprocess.call(
                check_cmd, shell=True, cwd=cwd,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            ) == 0
            if not already_installed:
                self._log.info("Installing %s" % package)
                cmd = "%s %s" % (install_cmd, package)
                result = subprocess.call(cmd, shell=True, cwd=cwd)
                if result != 0:
                    self._log.warning('Failed to install [%s]' % package)
                    return False
        return True

    def _install_bundle(self, brew_files):
        cwd = self._context.base_directory()
        for f in brew_files:
            self._log.info("Installing from file %s" % f)
            cmd = "brew bundle --verbose --file=%s" % f
            result = subprocess.call(cmd, shell=True, cwd=cwd)
            if result != 0:
                self._log.warning('Failed to install file [%s]' % f)
                return False
        return True

    def _start_services(self, services_list):
        cwd = self._context.base_directory()
        for service in services_list:
            self._log.info("Starting service %s" % service)
            cmd = "brew services start %s" % service
            result = subprocess.call(cmd, shell=True, cwd=cwd)
            if result != 0:
                self._log.warning('Failed to start service [%s]' % service)
                return False
        self._log.info('All services have been started')
        return True

    def _bootstrap(self, cmd):
        subprocess.call(
            cmd, shell=True, cwd=self._context.base_directory(),
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

    def _bootstrap_brew(self):
        link = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
        # Handle brew in different locations:
        # - /opt/homebrew/bin/brew (Apple Silicon macOS)
        # - /usr/local/bin/brew (Intel macOS)
        # - /home/linuxbrew/.linuxbrew/bin/brew (Linux)
        cmd = """
            _setup_brew_env() {{
                if [ -x /opt/homebrew/bin/brew ]; then
                    eval "$(/opt/homebrew/bin/brew shellenv)"
                elif [ -x /usr/local/bin/brew ]; then
                    eval "$(/usr/local/bin/brew shellenv)"
                elif [ -x /home/linuxbrew/.linuxbrew/bin/brew ]; then
                    eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
                fi
            }}
            if command -v brew >/dev/null 2>&1; then
                brew update
            else
                _setup_brew_env
                if command -v brew >/dev/null 2>&1; then
                    brew update
                else
                    /bin/bash -c "$(curl -fsSL {0})"
                    _setup_brew_env
                    brew update
                fi
            fi
        """.format(link)
        self._bootstrap(cmd)
