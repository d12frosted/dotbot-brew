import os, subprocess, dotbot
from brew import Brew

class Cask(dotbot.Plugin):
    _directive = "cask"

    def can_handle(self, directive):
        return directive == self._directive

    def handle(self, directive, data):
        if directive != self._directive:
            raise ValueError('Cask cannot handle directive %s' %
                directive)
        return self._process_commands(data)

    def _process_commands(self, data):
        success = True
        defaults = self._context.defaults().get('shell', {})
        self.bootstrap(self)
        with open(os.devnull, 'w') as devnull:
            for item in data:
                stdin = stdout = stderr = devnull
                cmd = "brew cask install %s" % item
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

    @staticmethod
    def bootstrap(self):
        Brew.bootstrap(self)
        cmd = "brew tap caskroom/cask"
        with open(os.devnull, 'w') as devnull:
            stdin = stdout = stderr = devnull
            subprocess.call(cmd, shell=True, stdin=stdin, stdout=stdout, stderr=stderr)
