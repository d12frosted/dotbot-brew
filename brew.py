import os, subprocess, dotbot

class Brew(dotbot.Plugin):
    _brewDirective = "brew"
    _caskDirective = "cask"
    _tapDirective = "tap"

    def can_handle(self, directive):
        return directive in (self._tapDirective, self._brewDirective, self._caskDirective)

    def handle(self, directive, data):
        if directive == self._tapDirective:
            self._bootstrap_brew()
            return self._tap(data)
        if directive == self._brewDirective:
            self._bootstrap_brew()
            return self._process_data("brew install", data)
        if directive == self._caskDirective:
            self._bootstrap_cask()
            return self._process_data("brew cask install", data)
        raise ValueError('Brew cannot handle directive %s' % directive)

    def _tap(self, tap_list):
        cwd = self._context.base_directory()
        log = self._log

        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            for tap in tap_list:
                log.info("Tapping %s" % tap)
                cmd = "brew tap %s" % (tap)
                result = subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)

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
                cmd = "brew --cellar %s" % package
                isInstalled = subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)
                if isInstalled != 0:
                    log.info("Installing %s" % package)
                    cmd = "%s %s" % (install_cmd, package)
                    result = subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr, cwd=cwd)
                    if result != 0:
                        log.warning('Failed to install [%s]' % package)
                        return False
            return True

    def _bootstrap(self, cmd):
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr,
                            cwd=self._context.base_directory())

    def _bootstrap_brew(self):
        cmd = """hash brew || {
          ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
          brew update
        }"""
        self._bootstrap(cmd)

    def _bootstrap_cask(self):
        self._bootstrap_brew()
        cmd = "brew tap caskroom/cask"
        self._bootstrap(cmd)
