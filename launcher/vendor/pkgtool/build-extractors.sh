#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$HERE/../ps4-pkg-tools"
BUILD_ROOT="${PKGTOOL_BUILD_ROOT:-$HERE/.build}"
JOBS="${PKGTOOL_BUILD_JOBS:-2}"

if [[ ! -f "$SOURCE/CMakeLists.txt" ]]; then
    echo "Missing ps4-pkg-tools source at $SOURCE" >&2
    exit 1
fi

cmake -S "$SOURCE" -B "$BUILD_ROOT/linux" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release -DBUILD_PKG_QT_GUI=OFF \
    -DCMAKE_C_FLAGS="-DNDEBUG" -DCMAKE_CXX_FLAGS="-DNDEBUG"
cmake --build "$BUILD_ROOT/linux" --target ps4-pkg-tool --parallel "$JOBS"
mkdir -p "$HERE/bin"
install -m 755 "$BUILD_ROOT/linux/ps4-pkg-tool" "$HERE/bin/ps4-pkg-tool"

if [[ ${BUILD_WINDOWS:-auto} == 0 ]]; then
    exit 0
fi

MINGW_BIN="${MINGW_BIN:-}"
if [[ -z $MINGW_BIN ]]; then
    MINGW_BIN=$(dirname "$(command -v x86_64-w64-mingw32-g++ || true)")
fi
if [[ ! -x "$MINGW_BIN/x86_64-w64-mingw32-g++" ]]; then
    if [[ ${BUILD_WINDOWS:-auto} == 1 ]]; then
        echo "MinGW-w64 x86_64 compiler not found; set MINGW_BIN or BUILD_WINDOWS=0." >&2
        exit 1
    fi
    echo "Windows extractor build skipped (MinGW-w64 not found)." >&2
    exit 0
fi

cmake -S "$SOURCE" -B "$BUILD_ROOT/windows" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$HERE/toolchains/mingw64.cmake" \
    -DMINGW_BIN="$MINGW_BIN" -DCMAKE_BUILD_TYPE=Release \
    -DBUILD_PKG_QT_GUI=OFF \
    -DCMAKE_C_FLAGS="-DNDEBUG" -DCMAKE_CXX_FLAGS="-DNDEBUG" \
    -DCMAKE_EXE_LINKER_FLAGS="-static -static-libgcc -static-libstdc++"
cmake --build "$BUILD_ROOT/windows" --target ps4-pkg-tool --parallel "$JOBS"
install -m 644 "$BUILD_ROOT/windows/ps4-pkg-tool.exe" "$HERE/bin/ps4-pkg-tool.exe"
echo "Built Linux and Windows PKG extractors in $HERE/bin."
