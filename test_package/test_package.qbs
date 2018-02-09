import qbs 1.0

Project {
	references: [ buildDirectory + '/../conanbuildinfo.qbs' ]
	Product {
		type: 'application'
		consoleApplication: true

		Depends { name: 'ConanBasicSetup' }

		Depends { name: 'cpp' }
		property string binDirectory: {
			return buildDirectory.substr(0, buildDirectory.lastIndexOf('/', buildDirectory.lastIndexOf('/') - 1)) + "/bin";
		}
		cpp.compilerPathByLanguage: {
			return {
				"c": binDirectory + '/clang',
				"cpp": binDirectory + '/clang++',
			};
		}
		cpp.cxxStandardLibrary: 'libstdc++'
		cpp.linkerPath: binDirectory + '/clang++'
		cpp.linkerWrapper: undefined
		cpp.minimumMacosVersion: '10.10'
		cpp.frameworkPaths: [ binDirectory + '/../lib' ]
		cpp.frameworks: [ 'QtCore' ]
		cpp.rpaths: [ binDirectory + '/../lib' ]
		cpp.target: 'x86_64-apple-macosx10.10'

		Depends { name: 'xcode' }
		xcode.sdk: 'macosx10.10'

		files: [ 'test_package.cc' ]
	}
}
