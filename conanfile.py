from conans import ConanFile, tools
import os
import platform

class QtConan(ConanFile):
    name = 'qt'
    source_version = '5.6.3'
    package_version = '7'
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

            # https://b33p.net/kosada/node/10205
            self.run('patch -p1 < ../../qmenu-checkmark-and-icon.patch')

            # https://bugreports.qt.io/browse/QTBUG-57788
            # https://b33p.net/kosada/node/7384
            self.run('patch -p1 -R < ../../qcocoaintegration-presentationoptions.patch')

            # https://bugreports.qt.io/browse/QTBUG-46701
            # https://b33p.net/kosada/node/11419
            self.run('patch -p1 < ../../qcocoawindow-fullscreen-close.patch')

            tools.replace_in_file('mkspecs/common/clang.conf',
                                  'QMAKE_CXXFLAGS_CXX11             = -std=c++11',
                                  'QMAKE_CXXFLAGS_CXX11             = -std=c++11 -stdlib=libc++')
            tools.replace_in_file('mkspecs/common/clang.conf',
                                  'QMAKE_LFLAGS_CXX11      =',
                                  'QMAKE_LFLAGS_CXX11      = -stdlib=libc++')

        self.run('mv %s/LICENSE.LGPLv21 %s/%s.txt' % (self.source_dir, self.source_dir, self.name))
        self.run('mv %s/LGPL_EXCEPTION.txt %s/%s-lgpl-exception.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        if platform.system() == 'Darwin':
            # Don't specify `-sdk` here, since that causes qmake to require that SDK on the client system, too.
            # https://bugreports.qt.io/browse/QTBUG-41238
            platform_flags = '-platform macx-clang -no-xcb -no-dbus'
        elif platform.system() == 'Linux':
            platform_flags = '-platform linux-clang -no-icu'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            self.run('../%s/configure -prefix %s/%s -opensource -confirm-license -release %s -c++std c++11 -no-ssse3 -no-sse4.1 -no-sse4.2 -no-avx -no-avx2 -no-qml-debug -qt-zlib -qt-libpng -qt-libjpeg -qt-pcre -no-eglfs -no-directfb -no-linuxfb -no-kms -no-glib -strip -nomake examples -no-sql-mysql -no-sql-sqlite -skip 3d -skip activeqt -skip androidextras -skip canvas3d -skip connectivity -skip declarative -skip doc -skip enginio -skip graphicaleffects -skip location -skip multimedia -skip quickcontrols -skip quickcontrols2 -skip sensors -skip serialbus -skip serialport -skip wayland -skip webchannel -skip webengine -skip websockets -skip webview -skip winextras -skip x11extras -skip xmlpatterns -D QT_NO_GESTURES'
                     % (self.source_dir,
                        self.build_dir,
                        self.install_dir,
                        platform_flags))
            self.run('make -j9')
            self.run('make install > /dev/null')

    def package(self):
        self.copy('*', src='%s/lib'     % self.install_dir, links=True, dst='lib')
        # Copy a second time, since the first time it doesn't copy all the framework symlinks.
        self.copy('*', src='%s/lib'     % self.install_dir, links=True, dst='lib')

        self.copy('*', src='%s/plugins' % self.install_dir, links=True, dst='plugins')
        self.copy('*', src='%s/mkspecs' % self.install_dir, links=True, dst='mkspecs')
        self.copy('*', src='%s/bin'     % self.install_dir, links=True, dst='bin')
        self.copy('*', src='%s/phrasebooks'  % self.install_dir, links=True, dst='phrasebooks')
        self.copy('*', src='%s/translations' % self.install_dir, links=True, dst='translations')

        self.copy('*', src='%s/include' % self.install_dir, dst='include')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')
        self.copy('%s-lgpl-exception.txt' % self.name, src=self.source_dir, dst='license')
