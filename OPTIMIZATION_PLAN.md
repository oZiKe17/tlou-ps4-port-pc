# Plan de Optimización — TLOU Port (PC/Linux)

**Objetivo:** subir FPS y estabilidad. El port arranca y muestra el juego, pero el rendimiento es bajo.

## Estado actual

- El juego corre (audio, threads, GPU). FPS reportado por el overlay (Fps | FrameTime | Gpu | Vram).
- **IMPORTANTE:** TLOU trata cualquier tamaño de memoria directa != 4608 MiB como devkit y asigna un arena de debug que no cabe. Forzar `TLG_DMEM_MB=4608` (retail). Ya configurado en `run_logged.sh`.
- Stubs: 81 con firma genérica `int name(void)` (algunos ya refinados, como sceFiberGetSelf).
- 37 NIDs sin nombre (cosméticos).
- Build: GCC 14, LTO ON, PGO off (no hay perfil recolectado).

## Diagnóstico rápido (haz esto primero)

1. Ejecuta con overlay visible (ya activado por defecto) y anota:
   - FPS promedio y mínimo
   - FrameTime (ms)
   - GPU % y VRAM usada
   - CPU % (activar item Cpu en overlay_items si no está)
2. Ejecuta con logging detallado:
   ```bash
   TLG_VERBOSE_LOG=2 TLG_GAME_DIR="..." bash run.sh 2>&1 | tee /tmp/tlou_run.log
   ```
3. Revisa `/tmp/tlou_run.log` al final (stats de runtime, stubs llamados, imports no resueltos).

## Niveles de optimización (de fácil a difícil)

### Nivel 1 — Configuración (sin recompilar)

Editar `tlg.ini` (se crea en el dir del port tras la primera ejecución) o pasar por env:

| Clave | Default | Optimizado | Efecto |
|---|---|---|---|
| `render_resolution` | native | 720p o 1440p | Renderiza a menor resolución, upscaler FSR la estira. Mayor impacto en GPU. |
| `engine_fps` | 120 | 60 | Menos frames por segundo = menos carga. |
| `async_shaders` | 1 | 1 (ya on) | Compila shaders en background. |
| `deferred_readback` | 1 | 1 (ya on) | Evita stalls de lectura. |
| `stale_readback` | 1 | 1 (ya on) | Reutiliza lecturas viejas. |
| `fps_limit` | 0 | 60 | Limita FPS para reducir carga. |
| `overlay_items` | Fps\|FrameTime\|Gpu\|Vram | Fps (solo) | Menos overhead del overlay. |

Ejemplo de `tlg.ini` optimizado:
```ini
render_resolution=720p
engine_fps=60
async_shaders=1
deferred_readback=1
stale_readback=1
fps_limit=60
show_fps=1
overlay_items=1
overlay_scale=80
```

### Nivel 2 — PGO (Profile-Guided Optimization)

Recolectar perfil de ejecución y recompilar con optimización basada en perfil.

```bash
# Paso 1: generar perfil (juega 2-3 minutos)
cd port
rm -rf pgo && mkdir pgo
TLG_PGO=generate TLG_GAME_DIR="..." bash run.sh
# (juega un rato, luego cierra el juego)

# Paso 2: recompilar con el perfil
TLG_PGO=use bash build.sh

# Paso 3: verificar mejora
TLG_GAME_DIR="..." bash run.sh
```

PGO típicamente da 10-20% de mejora en CPU.

### Nivel 3 — LTO (ya activo)

LTO ya está ON por defecto (`TLG_LTO=ON`). Si quieres desactivarlo para builds más rápidos (debug): `TLG_LTO=OFF bash build.sh`.

### Nivel 4 — FSR (upscaler)

El port incluye FSR 3/4. Para activarlo:
- En `tlg.ini`: `render_resolution=720p` (o 1080p si tu display es 4K) + activar FSR en el menú del port.
- FSR 4 requiere assets descargados (`tools/fsr4cap/build_assets.sh`).
- Verificar que `fsr4_411` esté presente en el directorio del port.

### Nivel 5 — Reducir carga de CPU (stubs)

Los stubs con firma genérica `int name(void)` causan overhead por mismatch de calling convention y llamadas a `fprintf(stderr, ...)`. Refinar las firmas más llamadas:
- Identificar stubs más llamados (TLG_VERBOSE_LOG=2 muestra llamadas).
- Reemplazar `tlou_stub()` (que hace fprintf) por implementaciones no-op sin logging.
- Priorizar stubs llamados en el hot path (render, audio, pad).

### Nivel 6 — Refinar código (largo plazo)

- Implementar los 81 stubs con firmas reales (usar Ghidra).
- Resolver los 37 NIDs sin nombre.
- Promover borrowables genéricos a ps4_core.
- Optimizar el path de memoria (guest_memset/memcpy ya tienen write-merge).

## Logging para diagnóstico

### Nivel de log (env var)
```bash
TLG_VERBOSE_LOG=0  # off (default)
TLG_VERBOSE_LOG=1  # básico (imports no resueltos, TTY init)
TLG_VERBOSE_LOG=2  # detallado (llamadas a stubs, region trace, etc.)
```

### Capturar a archivo
```bash
TLG_VERBOSE_LOG=2 TLG_GAME_DIR="..." bash run.sh 2>&1 | tee /tmp/tlou_$(date +%Y%m%d_%H%M%S).log
```

### Al final de la ejecución
El juego imprime un resumen completo (Runtime: ..., mutexes, threads, audio, files, memory operations). Este resumen es clave para diagnosticar cuellos de botella.

### Métricas a monitorear
- **FPS / FrameTime**: overlay (F10 para mostrar/ocultar).
- **GPU %**: overlay.
- **VRAM usada**: overlay.
- **Threads creados/salidos**: resumen final.
- **Mutex locks/unlocks**: resumen final (mismatch = deadlock).
- **Files opened/not found**: resumen final.
- **Memory operations**: resumen final (alto = overhead).

## Plan de acción sugerido

1. **Hoy:** Ejecutar con `TLG_VERBOSE_LOG=2` y capturar log. Anotar FPS, GPU %, VRAM.
2. **Hoy:** Probar `render_resolution=720p` + `engine_fps=60` en tlg.ini.
3. **Mañana:** Recolectar perfil PGO (jugar 3-5 min, luego recompilar con PGO=use).
4. **Esta semana:** Refinar stubs más llamados (eliminar fprintf, implementar no-op).
5. **Largo plazo:** Implementar stubs reales, resolver NIDs, promover a core.

## Archivos relevantes

- `tlg.ini` (se crea en el dir del port tras primera ejecución) — configuración.
- `out/gpu-build.log` — log del build de GPU.
- `out/tlg-probe` — binario.
- `port/src/runtime_tlou.c` — stubs (81).
- `port/src/runtime_gr2.c` — borrowables (fibers, jpeg, png, socket, etc.).
- `BORROWABLES.md` — tabla de borrowables.
- `OPTIMIZATION_PLAN.md` — este documento.
