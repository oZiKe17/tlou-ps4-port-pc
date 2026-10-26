PKG extraction
==============

The release packages use the GPL-2.0-or-later ps4-pkg-tools CLI bundled in
../ps4-pkg-tools/ and ./bin/. Rebuild both platform tools with
`./build-extractors.sh` (CMake, Ninja, C++23; MinGW-w64 for Windows cross-builds).
On Windows, `Build Windows.bat` builds the native Windows extractor as part of
the regular build. The corresponding source and upstream licenses are bundled.

PkgTool.Core.dll from PatchBuilder is proprietary SDK tooling and is not used
or distributed by this launcher.
