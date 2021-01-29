import os
import platform
import subprocess
import dotbot
class Brew(dotbot.Plugin):
    _brewDirective = "brew"
    _caskDirective = "cask"
    _tapDirective = "tap"
    _brewFileDirective = "brewfile"
    _defaults = {}
    _forceIntelOption = "force_intel"

    def can_handle(self, directive):
        return directive in (self._tapDirective, self._brewDirective, self._caskDirective, self._brewFileDirective)

    def handle(self, directive, data):
        self._defaults = self._context.defaults().get(directive, {})
        if directive == self._tapDirective:
            return self._tap(data)
        if directive == self._brewDirective:
            return self._brew(data)
        if directive == self._caskDirective:
            return self._cask(data)
        if directive == self._brewFileDirective:
            return self._brewfile(data)
        self._log.error("Didn't find directive %s", directive)
        raise ValueError('Brew cannot handle directive %s' % directive)

    def _invokeShellCommand(self, cmd):
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            if self._defaults.get('stdin', False) == True:
                stdin = None
            if self._defaults.get('stdout', False) == True:
                stdout = None
            if self._defaults.get('stderr', False) == True:
                stderr = None
            if self._defaults.get(self._forceIntelOption, False) == True:
                cmd = "arch --x86_64 " + cmd
            return subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr,
                                   cwd=self._context.base_directory())

    def _tap(self, tap_list):
        self._bootstrap_brew()
       
        for tap in tap_list:
            self._log.info("Tapping %s" % tap)
            cmd = "brew tap %s" % (tap)
            result = self._invokeShellCommand(cmd)
            if result != 0:
                self._log.warning('Failed to tap [%s]' % tap)
                return False
        return True

    def _brew(self, packages):
        self._bootstrap_brew()
        return self._processPackages("brew install %s",
                                     "brew ls --versions %s", packages)

    def _cask(self, packages):
        self._bootstrap_brew()
        self._bootstrap_cask()
        return self._processPackages("brew install --cask %s",
                                     "brew ls --cask --versions %s", packages)

    def _processPackages(self, install_format, check_installed_format, packages):
        for pkg in packages:
            install_cmd = install_format % (pkg)
            check_installed_cmd = check_installed_format % (pkg)
            if self._install(install_format, check_installed_format, pkg) == False:
                self._log.error('Some packages were not installed')
                return False
        self._log.info('All packages have been installed')
        return True

    def _install(self, install_format, check_installed_format, pkg):
        cwd = self._context.base_directory()
        with open(os.devnull, 'w') as devnull:
            isInstalled = subprocess.call(
                check_installed_format % (pkg),
                shell=True, stdin=devnull, stdout=devnull, stderr=devnull, cwd=cwd)
            if isInstalled != 0:
                self._log.info("Installing %s" % pkg)
                result = self._invokeShellCommand(
                    install_format % (pkg))
                if result != 0:
                    self._log.warning('Failed to install [%s]' % pkg)
                    return False
            else:
                self._log.info("%s already installed" % pkg)
            return True

    def _brewfile(self, brew_files):
        # this directive has opposite defaults re stdin/stderr/stdout
        self._defaults['stdin'] = self._defaults.get('stdin', True)
        self._defaults['stderr'] = self._defaults.get('stderr', True)
        self._defaults['stdout'] = self._defaults.get('stdout', True)
        self._bootstrap_brew()
        self._bootstrap_cask()
        for f in brew_files:
            self._log.info("Installing from file %s" % f)
            cmd = "brew bundle --verbose --file=%s" % f
            result = self._invokeShellCommand(cmd)

            if result != 0:
                self._log.warning('Failed to install file [%s]' % f)
                return False
        return True

    def _bootstrap_brew(self):
        self._log.info("Installing brew")
        link = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
        cmd = """[[ $(command -v brew) != "" ]] || /bin/bash -c "$(curl -fsSL {0})" """.format(
            link)
        return subprocess.call(cmd, shell=True, cwd=self._context.base_directory()) == 0

    def _bootstrap_cask(self):
        self._log.info("Installing cask")
        cmd = "brew tap homebrew/cask"
        return subprocess.call(cmd, shell=True, cwd=self._context.base_directory()) == 0
