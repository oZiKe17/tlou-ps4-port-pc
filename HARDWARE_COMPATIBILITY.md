# Hardware Compatibility — TLOU Port

## Minimum Requirements

| Component | Minimum | Recommended |
|---|---|---|
| CPU | SSE4.2, POPCNT, AVX (x86-64 v2) | Ryzen 5 / Intel i5 (6+ cores) |
| GPU | Vulkan 1.3 (any) | Dedicated GPU with 4+ GB VRAM |
| RAM | 8 GB | 16 GB |
| Storage | 60 GB (game files) | SSD recommended |
| OS | Linux (x86-64) | Ubuntu 24.04 / Mint 22+ |

## CPU Compatibility

The port requires these instruction sets (fatal if missing):
- **SSE4.2** (Intel Nehalem+, AMD Bulldozer+)
- **POPCNT** (Intel Nehalem+, AMD Barcelona+)
- **AVX** (Intel Sandy Bridge+, AMD Bulldozer+)

These are emulated if missing (rewritable sets):
- **MOVBE** (emulated on Sandy/Ivy Bridge)
- **BMI1** (emulated on Sandy/Ivy Bridge)
- **LZCNT** (emulated on Sandy/Ivy Bridge)
- **SSE4A** (emulated on Intel CPUs)
- **F16C** (emulated on Sandy Bridge)

Run `setup.sh` to check your CPU.

## GPU Compatibility

- **Vulkan 1.3** required (standard on all modern GPUs)
- **FSR 4** requires INT8 dot product extension (Vega+ or NVIDIA Pascal+)
  - Falls back to **FSR 3.1** automatically if not supported
- **FSR 3.1** works on all Vulkan 1.3 GPUs
- **DLSS** requires NVIDIA RTX (not implemented yet)

## GPU Performance (approximate)

| GPU | Expected FPS (native, no FSR) | With FSR 720p |
|---|---|---|
| Radeon Vega (integrated, Ryzen 4000G) | ~20 FPS | ~30-40 FPS |
| Intel UHD 630 (integrated) | ~10-15 FPS | ~20-30 FPS |
| Intel Arc A380 | ~30-40 FPS | ~50-70 FPS |
| GTX 1660 Super | ~40-50 FPS | ~60-80 FPS |
| RTX 3060 | ~60-80 FPS | ~100+ FPS |
| RX 6600 | ~50-60 FPS | ~80-100 FPS |

## Vendor-specific notes

- **NVIDIA:** DLSS available (not yet implemented). FSR 3.1 works.
- **AMD:** FSR 4 requires INT8 dot products (Vega+ / RDNA). Falls back to FSR 3.1 on older.
- **Intel:** Arc GPUs support FSR 4 (INT8). Integrated UHD may struggle. Vulkan drivers on Linux are good (Mesa).

## Dependencies

```bash
# Ubuntu/Mint/Debian
sudo apt install -y build-essential cmake ninja-build pkg-config \
    libvulkan-dev libavcodec-dev libavutil-dev libswscale-dev \
    python3 python3-tk git

# SDL3 (build from source)
git clone https://github.com/libsdl-org/SDL.git
cd SDL && mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc) && sudo make install && sudo ldconfig

# GCC 14
sudo add-apt-repository -y ppa:ubuntu-toolchain-r/test
sudo apt update && sudo apt install -y gcc-14 g++-14

# Optional: fmt, boost, zydis, xxhash, freetype (if not in apt)
# See setup.sh for details
```

## Build

```bash
cd port
bash setup.sh          # check dependencies
bash build.sh          # build (first time: ~5 min)
bash run.sh            # run
```

## Notes

- The port is **version-agnostic**: works with any game dump (1.00, 1.11, etc.)
- The user provides their own game dump (no game files included)
- Shader cache is per-machine (in port/user/cache/)
- Settings are per-user (in ~/.config/tlou-launcher/settings.json)
- The port auto-detects game folder, screen resolution, and GPU capabilities