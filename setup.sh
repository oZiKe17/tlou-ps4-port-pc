#!/usr/bin/env bash
# setup.sh — verifica dependencias y hardware para TLOU Port
set -euo pipefail
cd -- "$(dirname -- "$0")"
missing=0

# Include user-local packages (SDL3, fmt, boost, etc.)
if [[ -d "$HOME/.local/lib/pkgconfig" ]]; then
    export PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
fi
if [[ -d "$HOME/.local/lib" ]]; then
    export CMAKE_PREFIX_PATH="$HOME/.local${CMAKE_PREFIX_PATH:+:$CMAKE_PREFIX_PATH}"
fi

# CMake's --find-package leaves CMakeFiles in its working directory. Keep setup checks out of
# the repository so running setup.sh does not dirty the source tree.
cmake_package_exists() {
    local package=$1 temp status
    temp=$(mktemp -d "${TMPDIR:-/tmp}/tlou-cmake-find.XXXXXX") || return 1
    if (cd "$temp" && cmake --find-package -DNAME="$package" -DCOMPILER_ID=GNU -DLANGUAGE=CXX -DMODE=EXIST >/dev/null 2>&1); then
        status=0
    else
        status=1
    fi
    rm -rf "$temp"
    return "$status"
}

echo "=== TLOU Port — Setup Check ==="
echo ""

# OS
echo "-- OS --"
uname -s -r -m
echo ""

# CPU
echo "-- CPU --"
cpu_model=$(awk -F: '/^model name[[:space:]]*:/ {sub(/^[[:space:]]+/, "", $2); print $2; exit}' /proc/cpuinfo 2>/dev/null || true)
echo "${cpu_model:-CPU model unavailable}"
cpu_count=$(nproc 2>/dev/null || getconf _NPROCESSORS_ONLN 2>/dev/null || echo '?')
echo "Logical CPUs: $cpu_count"
cpu_flags=$(awk -F: '/^flags[[:space:]]*:/ {print $2; exit}' /proc/cpuinfo 2>/dev/null || true)
cpu_missing=0
for feature in sse3 ssse3 cx16 sse4_1 sse4_2 popcnt lahf_lm avx; do
    flag_alias=$feature
    if [[ $feature == sse3 ]]; then flag_alias=pni; fi # Linux exposes SSE3 as PNI.
    if [[ " $cpu_flags " == *" $feature "* || " $cpu_flags " == *" $flag_alias "* ]]; then
        echo "  $feature: OK"
    else
        echo "  $feature: MISSING (required by the portable host build/game)"
        cpu_missing=1
    fi
done
if (( cpu_missing )); then
    echo "  CPU compatibility: FAIL"
    missing=$((missing+1))
else
    echo "  CPU compatibility: OK"
fi
echo ""

# RAM
echo "-- RAM --"
free -h | grep Mem || true
ram_kib=$(awk '/^MemTotal:/ {print $2; exit}' /proc/meminfo 2>/dev/null || true)
ram_kib=${ram_kib:-0}
if (( ram_kib > 0 && ram_kib < 8*1024*1024 )); then
    echo "  Below documented 8 GiB minimum."
    missing=$((missing+1))
fi
echo ""

# GPU
echo "-- GPU --"
if command -v vulkaninfo >/dev/null 2>&1; then
    vulkaninfo --summary 2>/dev/null | grep -E "deviceName|deviceType|apiVersion" | head -4 || true
else
    echo "  vulkaninfo not found (install vulkan-tools)"
fi
echo ""

# Dependencies
echo "-- Dependencies --"
for tool in cmake ninja pkg-config python3 git; do
    if command -v "$tool" >/dev/null 2>&1; then
        ver=$($tool --version 2>/dev/null | head -1 | cut -d' ' -f3-4)
        echo "  $tool: OK ($ver)"
    else
        echo "  $tool: MISSING"
    fi
done
# Match build.sh's supported C++23 compiler selection instead of checking the system gcc only.
compiler_ok=0
if command -v gcc-14 >/dev/null 2>&1 && command -v g++-14 >/dev/null 2>&1; then
    echo "  C++ compiler: OK (GCC 14)"
    compiler_ok=1
elif command -v clang++-17 >/dev/null 2>&1; then
    echo "  C++ compiler: OK (Clang 17)"
    compiler_ok=1
elif command -v clang++-18 >/dev/null 2>&1; then
    echo "  C++ compiler: OK (Clang 18)"
    compiler_ok=1
elif command -v clang++ >/dev/null 2>&1; then
    clang_ver=$(clang++ --version 2>/dev/null | head -1 | grep -oE '[0-9]+' | head -1 || true)
    if [[ ${clang_ver:-0} =~ ^[0-9]+$ ]] && (( clang_ver >= 17 )); then
        echo "  C++ compiler: OK (Clang $clang_ver)"
        compiler_ok=1
    fi
fi
if (( ! compiler_ok )); then
    echo "  C++ compiler: MISSING (GCC 14+ or Clang 17+ required)"
    missing=$((missing+1))
fi
echo ""
echo "-- pkg-config libraries --"
for lib in vulkan sdl3 libavformat libavcodec libavutil libswscale libswresample freetype2 libxxhash; do
    if pkg-config --exists "$lib" 2>/dev/null; then
        ver=$(pkg-config --modversion "$lib" 2>/dev/null)
        echo "  $lib: OK ($ver)"
    else
        echo "  $lib: MISSING"
        missing=$((missing+1))
    fi
done
for package in fmt Boost tsl-robin-map; do
    if cmake_package_exists "$package"; then
        echo "  CMake $package: OK"
    else
        echo "  CMake $package: MISSING"
        missing=$((missing+1))
    fi
done
if command -v glslang >/dev/null 2>&1 || command -v glslangValidator >/dev/null 2>&1; then
    echo "  glslang: OK"
else
    echo "  glslang/glslangValidator: MISSING"
    missing=$((missing+1))
fi
if [[ -f /usr/include/vk_mem_alloc.h || -f /usr/include/vma/vk_mem_alloc.h || \
      -f /usr/local/include/vk_mem_alloc.h || -f /usr/local/include/vma/vk_mem_alloc.h || \
      -f "$HOME/.local/include/vk_mem_alloc.h" || -f "$HOME/.local/include/vma/vk_mem_alloc.h" ]] || \
   cmake_package_exists VulkanMemoryAllocator; then
    echo "  Vulkan Memory Allocator: OK"
else
    echo "  Vulkan Memory Allocator header/package: MISSING"
    missing=$((missing+1))
fi
if cmake_package_exists Zydis || pkg-config --exists zydis 2>/dev/null; then
    echo "  Zydis: OK"
else
    echo "  Zydis CMake/pkg-config package: MISSING"
    missing=$((missing+1))
fi
echo ""

# Optional
echo "-- Optional (for PKG extraction) --"
if command -v dotnet >/dev/null 2>&1; then
    echo "  dotnet: OK ($(dotnet --version))"
else
    echo "  dotnet: MISSING (needed for PKG extraction)"
fi
if [ -f "${PATCHBUILDER_DIR:-$HOME/PatchBuilderLinux}/engine/PkgTool.Core.dll" ]; then
    echo "  PkgTool.Core.dll: found"
else
    echo "  PkgTool.Core.dll: not found (PKG extraction unavailable)"
fi
echo ""

# Screen
echo "-- Display --"
if command -v xrandr >/dev/null 2>&1; then
    xrandr 2>/dev/null | grep '*' | head -1
else
    echo "  xrandr not found"
fi
echo ""

# Summary
echo "=== Summary ==="
for tool in cmake ninja pkg-config python3 git; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "  MISSING: $tool"
        missing=$((missing+1))
    fi
done
if [ $missing -eq 0 ]; then
    echo "  All dependencies OK. Ready to build."
else
    echo "  $missing missing dependencies. Install them first."
fi
echo ""
echo "Hardware requirements:"
echo "  CPU: x86-64-v2 plus AVX (required). MOVBE/BMI1/LZCNT/SSE4A/F16C (emulated if missing)."
echo "  GPU: Vulkan 1.3+ (FSR 4 needs INT8 dot products; falls back to FSR 3.1)."
echo "  RAM: 8 GB minimum, 16 GB recommended."
echo "  Storage: ~60 GB for game files."
(( missing == 0 )) || exit 1
