from conans import ConanFile, tools
import os
import platform

class QtConan(ConanFile):
    name = 'qt'
    source_version = '5.11.3'
    package_version = '0'
    version = '%s-%s' % (source_version, package_version)

    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://qt.io/'
    license = 'http://doc.qt.io/qt-5/opensourcelicense.html'
    description = 'Cross-platform application framework'
    source_dir = 'qt-everywhere-src-%s' % source_version
    build_dir = '_build'
    install_dir = '_install'
    exports_sources = '*.patch'

    def source(self):
        tools.get('http://download.qt.io/new_archive/qt/5.11/%s/single/qt-everywhere-src-%s.tar.xz' % (self.source_version, self.source_version),
            md5='02b353bfe7a40a8dc4274e1d17226d2b')

        with tools.chdir('%s/qtbase' % self.source_dir):
            # https://bugreports.qt.io/browse/QTBUG-26795
            # Status: merged in Qt 5.12.
            self.run('patch -p1 < ../../qgraphicsscene-device-pixel-ratio.patch')

            # https://bugreports.qt.io/browse/QTBUG-31406
            # https://b33p.net/kosada/node/6228
            # https://vuo.org/node/111
            # Status: maybe fixed in Qt 5.12?
            self.run('patch -p1 < ../../qcolordialog-position.patch')

            # https://bugreports.qt.io/browse/QTBUG-46351
            # https://b33p.net/kosada/node/12358
            # Status: unresolved as of 2020.07.31.
            self.run('patch -p0 < ../../qapplication-ignore-touchbegin.patch')

            # https://bugreports.qt.io/browse/QTBUG-63681
            # https://b33p.net/kosada/node/13245
            # Status: merged in Qt 5.12.
            self.run('patch -p0 < ../../qwheelevent-timestamp.patch')

            # https://bugreports.qt.io/browse/QTBUG-59805
            # https://b33p.net/kosada/node/13956
            # Status: unresolved as of 2020.07.31.
            self.run('patch -p0 < ../../qfiledialog-message.patch')

            # https://b33p.net/kosada/node/10205
            # https://bugreports.qt.io/browse/QTBUG-66380
            # Status: merged in Qt 5.12, but reverted in 5.12.5
            # since other people want it to hide the checkmark when an icon is present.
            # The suggested workaround is to render an icon that contains the checkmark,
            # but that doesn't work for us since Qt scales down the icon to fit within 16x16,
            # so the checkmark and icon would be too small.
            self.run('patch -p1 < ../../qmenu-checkmark-and-icon.patch')

            # https://bugreports.qt.io/browse/QTBUG-57788
            # https://b33p.net/kosada/node/7384
            # Status: merged in Qt 5.14.
            self.run('patch -p1 -R < ../../qcocoaintegration-presentationoptions.patch')

            # https://b33p.net/kosada/node/14521
            self.run('patch -p1 < ../../qcocoaeventdispatcher-enable-gestures.patch')

            # https://bugreports.qt.io/browse/QTBUG-69955
            # https://b33p.net/kosada/node/14794
            # Status: merged in Qt 5.12.
            self.run('patch -p1 < ../../qcoretextfontdatabase-mojave.patch')

            # Enable qsslconfiguration.h to compile with Clang 3.3.
            self.run('patch -p0 < ../../qsslconfiguration-clang3.patch')

            tools.replace_in_file('mkspecs/common/clang.conf',
                                  'QMAKE_CXXFLAGS_CXX11             = -std=c++11',
                                  'QMAKE_CXXFLAGS_CXX11             = -std=c++11 -stdlib=libc++')
            tools.replace_in_file('mkspecs/common/clang.conf',
                                  'QMAKE_LFLAGS_CXX11      =',
                                  'QMAKE_LFLAGS_CXX11      = -stdlib=libc++')

            with open('mkspecs/common/clang.conf', 'a') as f:
                f.write('QMAKE_CFLAGS_RELEASE   = -Oz\n')
                f.write('QMAKE_CXXFLAGS_RELEASE = -Oz\n')
                f.write('QMAKE_LFLAGS_RELEASE   = -Oz\n')

        self.run('mv %s/LICENSE.LGPLv3 %s/%s.txt' % (self.source_dir, self.source_dir, self.name))
        self.run('mv %s/LGPL_EXCEPTION.txt %s/%s-lgpl-exception.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        if platform.system() == 'Darwin':
            # Qt 5.11 requires the macOS 10.12 SDK (it uses new-style enums like `NSEventTypeMouseMoved` and `NSWindowStyleMask`).
            platform_flags = '\
                -platform macx-clang \
                -sdk macosx10.12 \
                -no-xcb \
                -no-dbus \
                -style-mac \
                -no-style-fusion \
            '
        elif platform.system() == 'Linux':
            platform_flags = '-platform linux-clang -no-icu'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        tools.mkdir(self.build_dir)
        with tools.chdir(self.build_dir):
            # `-style-windows` is required for Qt Stylesheets.
            self.run('../%s/configure -prefix %s/%s \
                -opensource -confirm-license \
                -release \
                -optimize-size \
                -strip \
                %s \
                -c++std c++11 \
                -no-ssse3 \
                -no-sse4.1 \
                -no-sse4.2 \
                -no-avx \
                -no-avx2 \
                -no-qml-debug \
                -style-windows \
                -system-zlib \
                -qt-libpng \
                -qt-libjpeg \
                -qt-pcre \
                -no-eglfs \
                -no-directfb \
                -no-linuxfb \
                -no-kms \
                -no-glib \
                -nomake examples \
                -no-sql-mysql \
                -no-sql-psql \
                -no-sql-sqlite \
                -no-freetype \
                -no-feature-cups \
                -no-feature-dial \
                -no-feature-ftp \
                -no-feature-fontconfig \
                -no-feature-freetype \
                -no-feature-imageformat_ppm \
                -no-feature-imageformat_xbm \
                -no-feature-lcdnumber \
                -no-feature-socks5 \
                -no-feature-statemachine \
                -no-feature-textodfwriter \
                -no-feature-udpsocket \
                -no-feature-tuiotouch \
                -skip 3d \
                -skip activeqt \
                -skip androidextras \
                -skip canvas3d \
                -skip charts \
                -skip connectivity \
                -skip datavis3d \
                -skip doc \
                -skip enginio \
                -skip gamepad \
                -skip graphicaleffects \
                -skip location \
                -skip networkauth \
                -skip purchasing \
                -skip remoteobjects \
                -skip script \
                -skip scxml \
                -skip sensors \
                -skip serialbus \
                -skip serialport \
                -skip speech \
                -skip virtualkeyboard \
                -skip wayland \
                -skip webchannel \
                -skip webengine \
                -skip webglplugin \
                -skip websockets \
                -skip webview \
                -skip winextras \
                -skip x11extras \
                -skip xmlpatterns \
                '
                     % (self.source_dir,
                        self.build_folder, # Not a typo - this is the absolute path to the Conan build folder root (not the self.build_dir subfolder).
                        self.install_dir,
                        platform_flags))
            self.run('make -j9 | tail -n 100')
            self.run('make install > /dev/null')

    def package(self):
        self.copy('*', src='%s/lib'     % self.install_dir, links=True, dst='lib')
        # Copy a second time, since the first time it doesn't copy all the framework symlinks.
        self.copy('*', src='%s/lib'     % self.install_dir, links=True, dst='lib')

        self.copy('*', src='%s/plugins' % self.install_dir, links=True, dst='plugins')
        self.copy('*', src='%s/mkspecs' % self.install_dir, links=True, dst='mkspecs')
        self.copy('*', src='%s/bin'     % self.install_dir, links=True, dst='bin')
        self.copy('*', src='%s/phrasebooks'  % self.install_dir, links=True, dst='phrasebooks')
        self.copy('*', src='%s/qml'          % self.install_dir, links=True, dst='qml')
        self.copy('*', src='%s/translations' % self.install_dir, links=True, dst='translations')

        self.copy('*', src='%s/include' % self.install_dir, dst='include')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')
        self.copy('%s-lgpl-exception.txt' % self.name, src=self.source_dir, dst='license')
