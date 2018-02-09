from conans import ConanFile, tools
import os

class QtConan(ConanFile):
    name = 'qt'
    source_version = '5.6.3'
    package_version = '1'
    version = '%s-%s' % (source_version, package_version)

    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://qt.io/'
    license = 'http://doc.qt.io/qt-5/opensourcelicense.html'
    description = 'Cross-platform application framework'
    source_dir = 'qt-everywhere-opensource-src-%s' % source_version
    build_dir = '_build'
    install_dir = '_install'
    exports_sources = '*.patch'

    def source(self):
        # Conan's `tools.get` doesn't yet support xz.
        # https://github.com/conan-io/conan/issues/52
        url = 'http://download.qt.io/official_releases/qt/5.6/%s/single/qt-everywhere-opensource-src-%s.tar.xz' % (self.source_version, self.source_version)
        filename = os.path.basename(url)
        tools.download(url, filename)
        tools.check_md5(filename, '010342d515b62ee1c0e709254f4ef9ab')
        self.run('xz -d "%s"' % filename)
        filename_tar = os.path.splitext(filename)[0]
        self.run('tar xf "%s"' % filename_tar)
        os.unlink(filename_tar)

        with tools.chdir('%s/qtbase' % self.source_dir):
            # https://bugreports.qt.io/browse/QTBUG-26795
            self.run('patch -p1 < ../../qgraphicsscene-device-pixel-ratio.patch')

            # https://bugreports.qt.io/browse/QTBUG-44620
            # https://b33p.net/kosada/node/11273
            self.run('patch -p1 < ../../qcolordialog-size.patch')

            # https://bugreports.qt.io/browse/QTBUG-31406
            # https://b33p.net/kosada/node/6228
            # https://vuo.org/node/111
            self.run('patch -p1 < ../../qcolordialog-position.patch')

            # https://bugreports.qt.io/browse/QTBUG-46351
            # https://b33p.net/kosada/node/12358
            self.run('patch -p0 < ../../qapplication-ignore-touchbegin.patch')

            # https://bugreports.qt.io/browse/QTBUG-63681
            # https://b33p.net/kosada/node/13245
            self.run('patch -p0 < ../../qwheelevent-timestamp.patch')

            # https://bugreports.qt.io/browse/QTBUG-59805
            # https://b33p.net/kosada/node/13956
            self.run('patch -p0 < ../../qfiledialog-message.patch')

    def build(self):
        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            self.run('../%s/configure -prefix %s/%s -opensource -confirm-license -release -silent -no-ssse3 -no-sse4.1 -no-sse4.2 -no-avx -no-avx2 -no-qml-debug -qt-zlib -qt-libpng -qt-libjpeg -qt-pcre -no-xcb -no-eglfs -no-directfb -no-linuxfb -no-kms -no-glib -strip -no-dbus -nomake tools -nomake examples -no-sql-mysql -no-sql-sqlite -skip 3d -skip activeqt -skip androidextras -skip canvas3d -skip connectivity -skip declarative -skip doc -skip enginio -skip graphicaleffects -skip location -skip multimedia -skip quickcontrols -skip quickcontrols2 -skip sensors -skip serialbus -skip serialport -skip tools -skip translations -skip wayland -skip webchannel -skip webengine -skip websockets -skip webview -skip winextras -skip x11extras -skip xmlpatterns -D QT_NO_GESTURES'
                     % (self.source_dir,
                        self.build_folder,
                        self.install_dir))
            self.run('make -j9 > /dev/null')
            self.run('make install > /dev/null')

    def package(self):
        self.copy('*', src='%s/lib'     % self.install_dir, links=True, dst='lib')
        # Copy a second time, since the first time it doesn't copy all the framework symlinks.
        self.copy('*', src='%s/lib'     % self.install_dir, links=True, dst='lib')

        self.copy('*', src='%s/plugins' % self.install_dir, links=True, dst='plugins')
        self.copy('*', src='%s/mkspecs' % self.install_dir, links=True, dst='mkspecs')
        self.copy('*', src='%s/bin'     % self.install_dir, links=True, dst='bin')
