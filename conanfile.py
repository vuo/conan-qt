from conans import ConanFile, tools
import os
import platform
import shutil

class QtConan(ConanFile):
    name = 'qt'
    source_version = '5.11.3'
    package_version = '4'
    version = '%s-%s' % (source_version, package_version)

    build_requires = (
        'llvm/5.0.2-1@vuo/stable',
        'macos-sdk/11.0-0@vuo/stable',
    )
    settings = 'os', 'compiler', 'build_type', 'arch'
    url = 'https://qt.io/'
    license = 'http://doc.qt.io/qt-5/opensourcelicense.html'
    description = 'Cross-platform application framework'
    source_dir = 'qt-everywhere-src-%s' % source_version

    build_x86_dir = '_build_x86'
    build_arm_dir = '_build_arm'
    build_arm_tools_dir = '_build_arm_tools'
    install_x86_dir = '_install_x86'
    install_arm_dir = '_install_arm'
    install_arm_tools_dir = '_install_arm_tools'
    install_universal_dir = '_install_universal'

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

            # https://bugreports.qt.io/browse/QTBUG-69204
            # Status: merged in Qt 5.12.6.
            self.run('patch -p1 < ../../qstylesheet-repolish-children0.patch')
            self.run('patch -p1 < ../../qstylesheet-repolish-children1.patch')

            tools.patch(patch_file='../../qcocoahelpers.patch')

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

            shutil.copytree('mkspecs/macx-clang', 'mkspecs/macx-arm64-clang')
            tools.replace_in_file('mkspecs/macx-arm64-clang/qmake.conf', 'QMAKE_APPLE_DEVICE_ARCHS = x86_64', 'QMAKE_APPLE_DEVICE_ARCHS = arm64')

        self.run('mv %s/LICENSE.LGPLv3 %s/%s.txt' % (self.source_dir, self.source_dir, self.name))
        self.run('mv %s/LGPL_EXCEPTION.txt %s/%s-lgpl-exception.txt' % (self.source_dir, self.source_dir, self.name))

    def build(self):
        # `-style-windows` is required for Qt Stylesheets.
        configure_command = '../%s/configure \
            -opensource -confirm-license \
            -release \
            -optimize-size \
            -strip \
            -c++std c++11 \
            -no-ssse3 \
            -no-sse4.1 \
            -no-sse4.2 \
            -no-avx \
            -no-avx2 \
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
            -no-feature-futimens \
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
            ' % self.source_dir

        if platform.system() == 'Darwin':
            configure_command += '\
                -sdk macosx11.0 \
                -no-xcb \
                -no-dbus \
                -style-mac \
                -no-style-fusion \
            '
        elif platform.system() == 'Linux':
            configure_command += '-platform linux-clang -no-icu'
        else:
            raise Exception('Unknown platform "%s"' % platform.system())

        build_root = os.getcwd()

        self.output.info("=== Build for x86_64 ===")
        tools.mkdir(self.build_x86_dir)
        with tools.chdir(self.build_x86_dir):
            configure_command_full = '%s -prefix %s/%s \
                -no-qml-debug \
                -platform macx-clang \
                ' % (configure_command, build_root, self.install_x86_dir)
            self.output.info(configure_command_full)
            self.run(configure_command_full)
            self.run('make --quiet -j9')
            self.run('make --quiet install')

        self.output.info("=== Build for arm64 ===")
        tools.mkdir(self.build_arm_dir)
        with tools.chdir(self.build_arm_dir):
            configure_command_full = '%s -prefix %s/%s \
                -no-qml-debug \
                -platform macx-clang \
                -xplatform macx-arm64-clang \
                ' % (configure_command, build_root, self.install_arm_dir)
            self.output.info(configure_command_full)
            self.run(configure_command_full)
            self.run('make --quiet -j9')
            self.run('make --quiet install')

        self.output.info("=== Build tools for arm64 ===")
        # Above, Qt built some of the qttools for the host system (x86_64)
        # since it needs to run them in order to build other Qt components.
        # Now build the qttools for arm64.
        tools.mkdir(self.build_arm_tools_dir)
        with tools.chdir(self.build_arm_tools_dir):
            configure_command_full = '%s -prefix %s/%s \
                -platform macx-arm64-clang \
                -xplatform macx-arm64-clang \
                -skip declarative \
                -skip imageformats \
                -skip macextras \
                -skip multimedia \
                -skip quickcontrols \
                -skip quickcontrols2 \
                -skip svg \
                ' % (configure_command, build_root, self.install_arm_tools_dir)
            self.output.info(configure_command_full)
            self.run(configure_command_full)
            # Create the makefiles.
            self.run('make --quiet -j9 qmake_all')
            # Hack the makefiles to run the host's tools (rather than trying to run the ARM tools on X86).
            for f in [
                'moc',
                'qfloat16-tables',
                'qvkgen',
                'rcc',
                'uic',
            ]:
                self.run("find . \\( -name Makefile -or -name uic_wrapper.sh -or -name qvkgen_wrapper.sh \\) -print0 | xargs -0 perl -pi -e 's/_build_arm_tools\\/qtbase\\/bin\\/%s/_build_x86\\/qtbase\\/bin\\/%s/g;'" % (f, f))
            # Build.
            self.run('make --quiet -j9 module-qttools')

    def package(self):
        tools.mkdir(self.install_universal_dir)
        with tools.chdir(self.install_universal_dir):
            tools.mkdir('bin')
            with tools.chdir('bin'):
                for f in [
                    'moc',
                    'rcc',
                    'uic',
                ]:
                    self.run('lipo -create ../../%s/bin/%s ../../%s/qtbase/bin/%s -output %s' % (self.install_x86_dir, f, self.build_arm_tools_dir, f, f))
                    self.run('codesign --sign - %s' % f)
                for f in [
                    'lconvert',
                    'lrelease',
                    'lupdate',
                ]:
                    self.run('lipo -create ../../%s/bin/%s ../../%s/qttools/bin/%s -output %s' % (self.install_x86_dir, f, self.build_arm_tools_dir, f, f))
                    self.run('codesign --sign - %s' % f)

            tools.mkdir('lib')
            with tools.chdir('lib'):
                self.run('cp -a ../../%s/lib/cmake .' % self.install_x86_dir)
                for f in [
                    'QtCore',
                    'QtGui',
                    'QtMacExtras',
                    'QtMultimedia',
                    'QtMultimediaQuick',
                    'QtMultimediaWidgets',
                    'QtNetwork',
                    'QtOpenGL',
                    'QtPrintSupport',
                    'QtQml',
                    'QtQuick',
                    'QtSvg',
                    'QtTest',
                    'QtWidgets',
                    'QtXml',
                ]:
                    self.run('cp -a ../../%s/lib/%s.framework .' % (self.install_x86_dir, f))
                    self.run('lipo -create ../../%s/lib/%s.framework/Versions/5/%s ../../%s/lib/%s.framework/Versions/5/%s -output %s.framework/Versions/5/%s' % (
                        self.install_x86_dir, f, f,
                        self.install_arm_dir, f, f,
                        f, f))
                    self.run('codesign --sign - %s.framework/Versions/5/%s' % (f, f))

            self.run('cp -a ../%s/plugins ../%s/qml .' % (self.install_x86_dir, self.install_x86_dir))
            for dirpath, dirnames, files in os.walk('.'):
                for name in files:
                    if name.endswith('.dylib') and name != 'libqquickwidget.dylib':
                        path = os.path.join(dirpath, name)
                        self.run('lipo -create ../%s/%s ../%s/%s -output %s' % (self.install_x86_dir, path, self.install_arm_dir, path, path))
                        self.run('codesign --sign - %s' % path)

        for f in [
            'moc',
            'rcc',
            'uic',
            'lconvert',
            'lrelease',
            'lupdate',
        ]:
            self.copy(f, src='%s/bin' % self.install_universal_dir, links=True, dst='bin')

        # qmake is needed by Qt5CoreConfig.cmake..?
        self.copy('qmake', src='%s/bin' % self.install_x86_dir, links=True, dst='bin')

        self.copy('*', src='%s/lib'     % self.install_universal_dir, links=True, dst='lib')
        # Copy a second time, since the first time it doesn't copy all the framework symlinks.
        self.copy('*', src='%s/lib'     % self.install_universal_dir, links=True, dst='lib')

        self.copy('*', src='%s/plugins' % self.install_universal_dir, links=True, dst='plugins')
        self.copy('*', src='%s/mkspecs' % self.install_x86_dir, links=True, dst='mkspecs')
        self.copy('*', src='%s/phrasebooks'  % self.install_x86_dir, links=True, dst='phrasebooks')
        self.copy('*', src='%s/qml'          % self.install_universal_dir, links=True, dst='qml')
        self.copy('*', src='%s/translations' % self.install_x86_dir, links=True, dst='translations')

        self.copy('*', src='%s/include' % self.install_x86_dir, dst='include')

        self.copy('%s.txt' % self.name, src=self.source_dir, dst='license')
        self.copy('%s-lgpl-exception.txt' % self.name, src=self.source_dir, dst='license')
