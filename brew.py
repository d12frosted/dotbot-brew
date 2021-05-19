import os, platform, subprocess, dotbot, sys

class Brew(dotbot.Plugin):
    _brewDirective = "brew"
    _caskDirective = "cask"
    _tapDirective = "tap"
    _brewFileDirective = "brewfile"

    def can_handle(self, directive):
        return directive in (self._tapDirective, self._brewDirective, self._caskDirective, self._brewFileDirective)

    def handle(self, directive, data):
        if directive == self._tapDirective:
            self._bootstrap_brew()
            return self._tap(data)
        if directive == self._brewDirective:
            self._bootstrap_brew()
            return self._process_data("brew install", data)
        if directive == self._caskDirective:
            if sys.platform.startswith("darwin"):
                self._bootstrap_cask()
                return self._process_data("brew install --cask", data)
            else:
                return True
        if directive == self._brewFileDirective:
            self._bootstrap_brew()
            self._bootstrap_cask()
            return self._install_bundle(data)
        raise ValueError('Brew cannot handle directive %s' % directive)

    def _tap(self, tap_list):
        cwd = self._context.base_directory()
        log = self._log
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            for tap in tap_list:
                log.info("Tapping %s" % tap)
                cmd = "brew tap %s" % (tap)
                result = subprocess.call(cmd, shell=True, cwd=cwd)

                if result != 0:
                    log.warning('Failed to tap [%s]' % tap)
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
        log = self._log
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            for package in packages_list:
                if install_cmd == 'brew install':
                    cmd = "brew ls --versions %s" % package
                else:
                    cmd = "brew cask ls --versions %s" % package
                isInstalled = subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)
                if isInstalled != 0:
                    log.info("Installing %s" % package)
                    cmd = "%s %s" % (install_cmd, package)
                    result = subprocess.call(cmd, shell=True, cwd=cwd)
                    if result != 0:
                        log.warning('Failed to install [%s]' % package)
                        return False
            return True

    def _install_bundle(self, brew_files):
        cwd = self._context.base_directory()
        log = self._log
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            for f in brew_files:
                log.info("Installing from file %s" % f)
                cmd = "brew bundle --file=%s" % f
                result = subprocess.call(cmd, shell=True, cwd=cwd)

                if result != 0:
                    log.warning('Failed to install file [%s]' % f)
                    return False
            return True

    def _bootstrap(self, cmd):
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr,
                            cwd=self._context.base_directory())

    def _bootstrap_brew(self):
        link = "https://raw.githubusercontent.com/Homebrew/install/master/install.sh"
        cmd = """hash brew || /bin/bash -c "$(curl -fsSL {0})";
              brew update""".format(link)
        self._bootstrap(cmd)

    def _bootstrap_cask(self):
        self._bootstrap_brew()
        cmd = "brew tap caskroom/cask"
        self._bootstrap(cmd)
