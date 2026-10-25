# tlou_pc — The Last of Us Remastered (PS4 → PC/Linux)

Port nativo de *The Last of Us™ Remastered* (CUSA00552, v1.00) para PC/Linux,
siguiendo el mismo patrón que `tlg_pc` / `gr2_pc` / `iss_pc`:

- `ps4_core` como núcleo compartido (compatibilidad PS4→host).
- `port/scripts/prepare.py` extrae imports del SELF y genera `out/boot.bin` + `out/analysis.json`.
- `port/scripts/link_modules.py` vincula `libc.prx`/`libSceFios2.prx` → `out/link.json` (imports no resueltos).
- `port/src/runtime_tlou.c` implementa los imports faltantes (stubs iniciales; refinar por función).
- Capa GPU: fork shadPS4 (GNM → Vulkan) en `port/gpu/` (sincronizar desde `ps4_core` o `tlg_pc`).

## Estado actual

- Análisis completo: `port/out/analysis.json`, `port/out/link.json`.
- Cobertura vs ps4_core: 407/526 resueltos (77.4%), 119 faltantes.
- Stubs generados para los 119 faltantes en `port/src/runtime_tlou.c` (firmas genéricas `int name()`).
- 38 de los 119 son borrowables desde `runtime_gr2*`/`runtime_infamous*` (marcados en el .c).
- 75 NIDs sin nombre: resolver con NID DB completa o RE.

## Próximos pasos

1. Sincronizar `port/gpu/` desde `ps4_core`/`tlg_pc` (submódulos third_party).
2. Promover a `ps4_core` las funciones borrowables genéricas (jpeg/png/fiber/socket).
3. Refinar firmas en `runtime_tlou.c` (SDK/RE) y reemplazar stubs por implementaciones.
4. Resolver los 75 NIDs sin nombre.
5. Compilar con `port/build.sh` y iterar.

