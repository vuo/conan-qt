from conans import ConanFile, tools
import os
import platform
import shutil

class QtTestConan(ConanFile):
    requires = 'llvm/3.3-5@vuo/stable'
    generators = 'qbs'

    def build(self):
        self.run('qbs -f "%s"' % self.source_folder)

    def imports(self):
        self.copy('*', src='bin', dst='bin')
        self.copy('*', src='lib', dst='lib')
        self.copy('*', src='plugins', dst='plugins')

        if platform.system() == 'Darwin':
            # Conan's `self.copy` doesn't copy symlinks to folders, so copy it ourselves.
            shutil.copytree(src='%s/lib' % self.deps_cpp_info["qt"].rootpath, dst='lib-qt', symlinks=True)
            shutil.rmtree('lib/QtCore.framework')
            shutil.move(src='lib-qt/QtCore.framework', dst='lib/QtCore.framework')
            shutil.rmtree('lib-qt')

    def checkDylib(self, dylibPath):
        if platform.system() == 'Darwin':
            self.run('! (otool -L %s | tail +3 | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")' % dylibPath)
            self.run('! (otool -L %s | fgrep "libstdc++")' % dylibPath)
            self.run('! (otool -l %s | grep -A2 LC_RPATH | cut -d"(" -f1 | grep "\s*path" | egrep -v "^\s*path @(executable|loader)_path")' % dylibPath)
        elif platform.system() == 'Linux':
            env_vars = {
                'LD_LIBRARY_PATH': '',
            }
            with tools.environment_append(env_vars):
                self.run('! (ldd %s | grep -v "^lib/" | grep "/" | egrep -v "(\s(/lib64/|(/usr)?/lib/x86_64-linux-gnu/)|test_package/build)")' % dylibPath)
                self.run('! (ldd %s | fgrep "libstdc++")' % dylibPath)

    def test(self):
        self.run('qbs run -f "%s"' % self.source_folder)

        # Ensure we only link to system libraries.
        for f in [
            'Concurrent',
            'Core',
            'Gui',
            'Network',
            'OpenGL',
            'Multimedia',
            'MultimediaQuick_p',
            'MultimediaWidgets',
            'PrintSupport',
            'Qml',
            'Quick',
            'QuickWidgets',
            'Script',
            'Sql',
            'Svg',
            'Test',
            'Widgets',
            'Xml',
        ]:
            self.output.info('Checking %s...' % f)
            if platform.system() == 'Darwin':
                self.checkDylib('lib/Qt%s.framework/Qt%s' % (f, f))
            elif platform.system() == 'Linux':
                self.checkDylib('lib/libQt5%s.so' % f)

        if platform.system() == 'Darwin':
            self.checkDylib('lib/QtMacExtras.framework/QtMacExtras')
            self.checkDylib('plugins/platforms/libqcocoa.dylib')
        elif platform.system() == 'Darwin':
            self.checkDylib('plugins/platforms/libqxcb.so')
