from conans import ConanFile, tools
import os
import shutil

class QtTestConan(ConanFile):
    requires = 'llvm/3.3-1@vuo/stable'
    generators = 'qbs'

    def build(self):
        self.run('qbs -f "%s"' % self.source_folder)

    def imports(self):
        self.copy('*', src='bin', dst='bin')
        self.copy('*', src='lib', dst='lib')
        self.copy('*', src='plugins', dst='plugins')

        # Conan's `self.copy` doesn't copy symlinks to folders, so copy it ourselves.
        shutil.copytree(src='%s/lib' % self.deps_cpp_info["qt"].rootpath, dst='lib-qt', symlinks=True)
        shutil.rmtree('lib/QtCore.framework')
        shutil.move(src='lib-qt/QtCore.framework', dst='lib/QtCore.framework')
        shutil.rmtree('lib-qt')

    def test(self):
        self.run('qbs run')

        # Ensure we only link to system libraries.
        for f in [
            'lib/QtConcurrent.framework/QtConcurrent',
            'lib/QtCore.framework/QtCore',
            'lib/QtGui.framework/QtGui',
            'lib/QtMacExtras.framework/QtMacExtras',
            'lib/QtNetwork.framework/QtNetwork',
            'lib/QtOpenGL.framework/QtOpenGL',
            'lib/QtPrintSupport.framework/QtPrintSupport',
            'lib/QtScript.framework/QtScript',
            'lib/QtSql.framework/QtSql',
            'lib/QtSvg.framework/QtSvg',
            'lib/QtTest.framework/QtTest',
            'lib/QtWidgets.framework/QtWidgets',
            'lib/QtXml.framework/QtXml',
            'plugins/platforms/libqcocoa.dylib',
        ]:
            self.run('! (otool -L ' + f + ' | tail +3 | egrep -v "^\s*(/usr/lib/|/System/|@rpath/)")')
