#!/usr/bin/env bash
# setup.sh — verifica dependencias y hardware para TLOU Port
set -euo pipefail
cd -- "$(dirname -- "$0")"

# Include user-local packages (SDL3, fmt, boost, etc.)
if [[ -d "$HOME/.local/lib/pkgconfig" ]]; then
    export PKG_CONFIG_PATH="$HOME/.local/lib/pkgconfig${PKG_CONFIG_PATH:+:$PKG_CONFIG_PATH}"
fi

echo "=== TLOU Port — Setup Check ==="
echo ""

# OS
echo "-- OS --"
uname -s -r -m
echo ""

# CPU
echo "-- CPU --"
grep -m1 "model name" /proc/cpuinfo
echo "Cores: $(nproc)"
# Check required instruction sets
for set in sse4_2 popcnt avx; do
    if grep -q "$set" /proc/cpuinfo 2>/dev/null || grep -qi "sse4_2\|popcnt\|avx" /proc/cpuinfo; then
        :
    fi
done
python3 -c "
import subprocess
out = subprocess.check_output(['cat','/proc/cpuinfo']).decode()
sets = {'sse4_2': 'SSE4.2', 'popcnt': 'POPCNT', 'avx': 'AVX'}
for s,name in sets.items():
    if s in out.lower():
        print(f'  {name}: OK')
    else:
        print(f'  {name}: MISSING (fatal - game will not run)')
" 2>/dev/null
echo ""

# RAM
echo "-- RAM --"
free -h | grep Mem
echo ""

# GPU
echo "-- GPU --"
if command -v vulkaninfo >/dev/null 2>&1; then
    vulkaninfo --summary 2>/dev/null | grep -E "deviceName|deviceType|apiVersion" | head -4
else
    echo "  vulkaninfo not found (install vulkan-tools)"
fi
echo ""

# Dependencies
echo "-- Dependencies --"
for tool in gcc g++ cmake ninja pkg-config python3 git; do
    if command -v "$tool" >/dev/null 2>&1; then
        ver=$($tool --version 2>/dev/null | head -1 | cut -d' ' -f3-4)
        echo "  $tool: OK ($ver)"
    else
        echo "  $tool: MISSING"
    fi
done
# GCC version check
if command -v gcc >/dev/null 2>&1; then
    gcc_ver=$(gcc -dumpversion)
    major=${gcc_ver%%.*}
    if [ "$major" -ge 14 ]; then
        echo "  gcc version: OK ($gcc_ver >= 14)"
    else
        echo "  gcc version: TOO OLD ($gcc_ver < 14) — install gcc-14"
    fi
fi
echo ""
echo "-- pkg-config libraries --"
for lib in vulkan sdl3 libavcodec libavutil libswscale freetype2; do
    if pkg-config --exists "$lib" 2>/dev/null; then
        ver=$(pkg-config --modversion "$lib" 2>/dev/null)
        echo "  $lib: OK ($ver)"
    else
        echo "  $lib: MISSING"
    fi
done
echo ""

# Optional
echo "-- Optional (for PKG extraction) --"
if command -v dotnet >/dev/null 2>&1; then
    echo "  dotnet: OK ($(dotnet --version))"
else
    echo "  dotnet: MISSING (needed for PKG extraction)"
fi
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
missing=0
for tool in gcc-14 g++-14 cmake ninja pkg-config; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "  MISSING: $tool"
        missing=$((missing+1))
    fi
done
for lib in vulkan sdl3 libavcodec libavutil libswscale freetype2; do
    if ! pkg-config --exists "$lib" 2>/dev/null; then
        echo "  MISSING: $lib"
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
echo "  CPU: SSE4.2, POPCNT, AVX (required). MOVBE/BMI1/LZCNT/SSE4A/F16C (emulated if missing)."
echo "  GPU: Vulkan 1.3+ (FSR 4 needs INT8 dot products; falls back to FSR 3.1)."
echo "  RAM: 8 GB minimum, 16 GB recommended."
echo "  Storage: ~60 GB for game files."