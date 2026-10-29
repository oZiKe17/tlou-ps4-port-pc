# tlou_pc — The Last of Us Remastered (PS4 → PC/Linux)

Native port of *The Last of Us™ Remastered* (CUSA00552, v1.00) to PC/Linux,
following the same pattern as `tlg_pc` / `gr2_pc` / `iss_pc`:

NO ORIGINAL GAME FILES OR ASSETS ARE PROVIDED

- `ps4_core` as the shared core (PS4→host compatibility).
- `port/scripts/prepare.py` extracts imports from the SELF and generates `out/boot.bin` + `out/analysis.json`.
- `port/scripts/link_modules.py` links `libc.prx`/`libSceFios2.prx` → `out/link.json` (unresolved imports).
- `port/src/runtime_tlou.c` implements the missing imports (initial stubs; refine per function).
- GPU layer: shadPS4 fork (GNM → Vulkan) in `port/gpu/` (sync from `ps4_core` or `tlg_pc`).

## Launcher: drag and drop

In **Game location**, drag the extracted folder containing `eboot.bin` or drop a `.pkg` file.
When dropping a PKG, the launcher opens the destination picker and continues with the extraction flow.
Linux and Windows x64 TkDND support is bundled in `launcher/vendor/tkinterdnd2/`.

PKG extraction uses the GPL-2.0-or-later CLI bundled in
`launcher/vendor/ps4-pkg-tools/` and `launcher/vendor/pkgtool/bin/`; it requires no .NET or the
proprietary `PkgTool.Core.dll` engine. To rebuild both binaries use
`launcher/vendor/pkgtool/build-extractors.sh`; on Windows, `Build Windows.bat` builds the native
CLI via MSYS2 CLANG64. Source code and licenses are distributed with the port.

## Current status

- Full analysis: `port/out/analysis.json`, `port/out/link.json`.
- Coverage vs ps4_core: 407/526 resolved (77.4%), 119 missing.
- Stubs generated for the 119 missing in `port/src/runtime_tlou.c` (generic signatures `int name()`).
- 38 of the 119 are borrowable from `runtime_gr2*`/`runtime_infamous*` (marked in the .c).
- 75 unnamed NIDs: resolve with full NID DB or RE.

## Test status

- Tested only on Linux (Ubuntu 24.04, Vulkan, PipeWire).
- Windows: build validated with MSYS2 CLANG64 for the runtime and the PKG extractor, but not run on Windows.
- macOS: not tested or supported.

## Known limitations

- Requires a legal copy of the game CUSA00552 (not included).
- 60 FPS and resolution patches for 1.00/1.11 require reverse engineering of the eboot (not included).
- FSR 4 requires a GPU with INT8 dot products; falls back to FSR 3.1.
- Hot pages disabled by default (observed FPS regression).

## MANY THINGS LEFT TO POLISH

1. Sync `port/gpu/` from `ps4_core`/`tlg_pc` (third_party submodules).
2. Promote generic borrowable functions to `ps4_core` (jpeg/png/fiber/socket).
3. Refine signatures in `runtime_tlou.c` (SDK/RE) and replace stubs with implementations.
4. Resolve the 75 unnamed NIDs.
5. Build with `port/build.sh` and iterate.



## Credits

This port is based on the work of several projects and communities:

- **SpartanPort** — [FelipePrado0/SpartanPort](https://github.com/FelipePrado0/SpartanPort): base of the PS4→PC port, launcher, shadPS4 GPU layer, and extraction tools.
- **shadPS4** — [shadps4-emu/shadPS4](https://github.com/shadps4-emu/shadPS4): PS4 emulator, GPU layer (GNM → Vulkan), shader recompiler.
- **ps4-pkg-tools** — [xXJSONDeruloXx/ps4-pkg-tools](https://github.com/xXJSONDeruloXx/ps4-pkg-tools): open-source PKG extractor (GPL-2.0-or-later), used for package extraction.
- **tkinterdnd2** — [Eliav2/tkinterdnd2](https://github.com/Eliav2/tkinterdnd2): drag-and-drop support in Tkinter (MIT).
- **LibAtrac9** — ATRAC9 decoder integrated into the port.
- **ps4_core** — shared core for PS4→host compatibility.


Thanks to the PS4→PC porting community and all contributors of the projects above.
