# tlou_pc — The Last of Us Remastered (PS4 → PC/Linux)

Port nativo de *The Last of Us™ Remastered* (CUSA00552, v1.00) para PC/Linux,
siguiendo el mismo patrón que `tlg_pc` / `gr2_pc` / `iss_pc`:

NO SE PROPORCIONA NINGUN ARCHIVO O ASSETS DEL JUEGO ORIGINAL

- `ps4_core` como núcleo compartido (compatibilidad PS4→host).
- `port/scripts/prepare.py` extrae imports del SELF y genera `out/boot.bin` + `out/analysis.json`.
- `port/scripts/link_modules.py` vincula `libc.prx`/`libSceFios2.prx` → `out/link.json` (imports no resueltos).
- `port/src/runtime_tlou.c` implementa los imports faltantes (stubs iniciales; refinar por función).
- Capa GPU: fork shadPS4 (GNM → Vulkan) en `port/gpu/` (sincronizar desde `ps4_core` o `tlg_pc`).

## Launcher: arrastrar y soltar

En **Ubicación del juego**, arrastra la carpeta extraída que contiene `eboot.bin` o suelta un archivo `.pkg`.
Al soltar un PKG, el launcher abre el selector de destino y continúa con el flujo de extracción.
El soporte TkDND x64 de Linux y Windows está incluido en `launcher/vendor/tkinterdnd2/`.

La extracción PKG usa el CLI GPL-2.0-or-later incluido en
`launcher/vendor/ps4-pkg-tools/` y `launcher/vendor/pkgtool/bin/`; no requiere .NET ni el motor
propietario `PkgTool.Core.dll`. Para reconstruir ambos binarios usa
`launcher/vendor/pkgtool/build-extractors.sh`; en Windows, `Build Windows.bat` construye el CLI
nativo mediante MSYS2 CLANG64. El código fuente y sus licencias se distribuyen con el port.

## Estado actual

- Análisis completo: `port/out/analysis.json`, `port/out/link.json`.
- Cobertura vs ps4_core: 407/526 resueltos (77.4%), 119 faltantes.
- Stubs generados para los 119 faltantes en `port/src/runtime_tlou.c` (firmas genéricas `int name()`).
- 38 de los 119 son borrowables desde `runtime_gr2*`/`runtime_infamous*` (marcados en el .c).
- 75 NIDs sin nombre: resolver con NID DB completa o RE.

## Estado de pruebas

- Probado solo en Linux (Ubuntu 24.04, Vulkan, PipeWire).
- Windows: compilación validada con MSYS2 CLANG64 para el runtime y el extractor PKG, pero no se ejecutó en Windows.
- macOS: no probado ni soportado.

## Limitaciones conocidas

- Requiere una copia legal del juego CUSA00552 (no incluida).
- Los parches de 60 FPS y resolución para 1.00/1.11 requieren reverse engineering del eboot (no incluidos).
- FSR 4 requiere GPU con INT8 dot products; fallback a FSR 3.1.
- Hot pages desactivado por defecto (regresión de FPS observada).
- El AppImage usa ~/.local/share/tlou-pc como directorio de datos escribible.

## Próximos pasos

1. Sincronizar `port/gpu/` desde `ps4_core`/`tlg_pc` (submódulos third_party).
2. Promover a `ps4_core` las funciones borrowables genéricas (jpeg/png/fiber/socket).
3. Refinar firmas en `runtime_tlou.c` (SDK/RE) y reemplazar stubs por implementaciones.
4. Resolver los 75 NIDs sin nombre.
5. Compilar con `port/build.sh` y iterar.

Ver plan completo: TLOU_PORT_PLAN.md (fuera del repo).
