import os, subprocess, dotbot

class Brew(dotbot.Plugin):
    _directive = "brew"

    def can_handle(self, directive):
        return directive == self._directive

    def handle(self, directive, data):
        if directive != self._directive:
            raise ValueError('Brew cannot handle directive %s' %
                directive)
        return self._process_commands(data)

    def _process_commands(self, data):
        success = True
        defaults = self._context.defaults().get('shell', {})
        self._bootstrap()
        with open(os.devnull, 'w') as devnull:
            for item in data:
                stdin = stdout = stderr = devnull
                cmd = "brew install %s" % item
                self._log.info("Installing %s" % item)
                ret = subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout,
                    stderr=stderr, cwd=self._context.base_directory())
                if ret != 0:
                    success = False
                    self._log.warning('Failed to install [%s]' % item)
        if success:
            self._log.info('All packages have been installed')
        else:
            self._log.error('Some packages were not installed')
        return success

    def _bootstrap(self):
        cmd = """hash brew || {
          ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
          brew update
        }"""
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout,
                            stderr=stderr, cwd=self._context.base_directory())
