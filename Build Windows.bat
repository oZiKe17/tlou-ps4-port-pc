@echo off
setlocal
cd /d "%~dp0"
if not exist "C:\msys64\msys2_shell.cmd" (
  echo MSYS2 not found at C:\msys64. Install from https://www.msys2.org/ first.
  pause & exit /b 1
)
set "PORT_BUILD=build.sh"
if exist "port\build.sh" set "PORT_BUILD=port/build.sh"
C:\msys64\msys2_shell.cmd -defterm -no-start -clang64 -c "cd '%CD:\=/%' && bash '%PORT_BUILD%' && cmake -S launcher/vendor/ps4-pkg-tools -B launcher/vendor/pkgtool/.build-win -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_PKG_QT_GUI=OFF && cmake --build launcher/vendor/pkgtool/.build-win --target ps4-pkg-tool && cp launcher/vendor/pkgtool/.build-win/ps4-pkg-tool.exe launcher/vendor/pkgtool/bin/ps4-pkg-tool.exe"
pause
