import os
import platform
import subprocess
import dotbot


class Brew(dotbot.Plugin):
    _installBrewDirective = "installBrew"
    _brewDirective = "brew"
    _caskDirective = "cask"
    _tapDirective = "tap"
    _brewFileDirective = "brewfile"

    _autoBootstrapOption = "auto_bootstrap"

    def can_handle(self, directive):
        return directive in (self._installBrewDirective, self._tapDirective, self._brewDirective, self._caskDirective, self._brewFileDirective)

    def handle(self, directive, data):
        defaults = self._context.defaults().get(directive, {})
        if directive == self._tapDirective:
            return self._tap(data, defaults)
        if directive == self._brewDirective:
            return self._brew(data, defaults)
        if directive == self._caskDirective:
            return self._cask(data, defaults)
        if directive == self._installBrewDirective:
            return self._installBrew(data)
        if directive == self._brewFileDirective:
            return self._brewfile(data, defaults)
        self._log.info("didn't found directive %s", directive)
        raise ValueError('Brew cannot handle directive %s' % directive)

    def _invokeShellCommand(self, cmd, defaults):
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            if defaults.get('stdin', False) == True:
                stdin = None
            if defaults.get('stdout', False) == True:
                stdout = None
            if defaults.get('stderr', False) == True:
                stderr = None
            subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr,
                            cwd=self._context.base_directory())

    def _tap(self, tap_list, defaults):
        if defaults.get(self._autoBootstrapOption, True) == True:
            self._bootstrap_brew()
        log = self._log
        for tap in tap_list:
            log.info("Tapping %s" % tap)
            cmd = "brew tap %s" % (tap)
            result = self._invoke(cmd, defaults)
            if result != 0:
                log.warning('Failed to tap [%s]' % tap)
                return False
        return True

    def _brew(self, packages, defaults):
        if defaults.get(self._autoBootstrapOption, True) == True:
            self._bootstrap_brew()
        return self._processPackages("brew install %s",
                                     "brew ls --versions %s", packages, defaults)

    def _cask(self, packages, defaults):
        if defaults.get(self._autoBootstrapOption, True) == True:
            self._bootstrap_brew()
            self._bootstrap_cask()
        return self._processPackages("brew install --cask %s",
                                     "brew ls --cask --versions %s", packages, defaults)

    def _processPackages(self, install_format, check_installed_format, packages, defaults):
        log = self._log
        for pkg in packages:
            install_cmd = install_format % (pkg)
            check_installed_cmd = check_installed_format % (pkg)
            if self._install(install_format, check_installed_format, pkg, defaults) == False:
                self._log.error('Some packages were not installed')
                return False
        self._log.info('All packages have been installed')
        return True

    def _install(self, install_format, check_installed_format, pkg, defaults):
        cwd = self._context.base_directory()
        log = self._log
        with open(os.devnull, 'w') as devnull:
            isInstalled = subprocess.call(
                check_installed_format % (pkg),
                shell=True, stdin=devnull, stdout=devnull, stderr=devnull, cwd=cwd)
            if isInstalled != 0:
                log.info("Installing %s" % pkg)
                result = self._invokeShellCommand(
                    install_format % (pkg), defaults)
                if result != 0:
                    log.warning('Failed to install [%s]' % pkg)
                    return False
            else:
                log.info("%s already installed" % pkg)
            return True

    def _brewfile(self, brew_files, defaults):
        log = self._log
        # this directive has opposite defaults re stdin/stderr/stdout
        defaults['stdin'] = defaults.get('stdin', True)
        defaults['stderr'] = defaults.get('stderr', True)
        defaults['stdout'] = defaults.get('stdout', True)
        if defaults.get(self._autoBootstrapOption, True) == True:
            self._bootstrap_brew()
            self._bootstrap_cask()
        stdin = stdout = stderr = devnull
        for f in brew_files:
            log.info("Installing from file %s" % f)
            cmd = "brew bundle --verbose --file=%s" % f
            result = self._invokeShellCommand(cmd, defaults)

            if result != 0:
                log.warning('Failed to install file [%s]' % f)
                return False

    def _installBrew(self, components):
        log = self._log
        for component in components:
            if component == "brew":
                self._bootstrap_brew()
            elif component == "cask":
                self._bootstrap_cask()
            else:
                log.error("Unknown component to install [%s]" % component)
                return False
        return True

    def _bootstrap_brew(self):
        self._log.info("Installing brew")
        link = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
        cmd = """[[ $(command -v brew) != "" ]] || /bin/bash -c "$(curl -fsSL {0})" """.format(link)
        return subprocess.call(cmd, shell=True, cwd=self._context.base_directory()) == 0

    def _bootstrap_cask(self):
        self._log.info("Installing cask")
        cmd = "brew tap homebrew/cask"
        return subprocess.call(cmd, shell=True, cwd=self._context.base_directory()) == 0
