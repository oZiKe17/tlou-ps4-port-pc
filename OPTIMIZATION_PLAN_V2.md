# Plan de Optimización Real V2 — TLOU Port

**Basado en:** SpartanPort (GoW3), tlg_pc, gr2_pc, iss_pc, uncharted_pc, ps4_core.
**Objetivo:** Maximizar FPS y estabilidad acercándose al original (PS4 30 FPS). Sin FSR, sin bajar resolución.

## Baseline actual

- **FPS:** ~19-20 FPS (native res, 60 Hz vblank)
- **CPU:** alto (recompiler + stubs + threads)
- **GPU:** ~? % (verificar overlay)
- **VRAM:** n/a (GPU no soporta VK_EXT_memory_budget)
- **Memory ops:** ~24M por sesión de 2 min
- **Threads:** ~200 creados
- **Budget:** 4608 MiB (retail)

## Lo que ya tenemos (aplicado)

| Optimización | Estado | Impacto |
|---|---|---|
| LTO (Link-Time Optimization) | ✅ ON por defecto | +5-10% CPU |
| -O3 -march=native (AVX2) | ✅ Aplicado | +5-10% CPU |
| Async shaders | ✅ ON por defecto | evita stalls de compilación |
| Deferred readback | ✅ ON por defecto | evita stalls de lectura |
| Stale readback | ✅ ON por defecto | reutiliza lecturas viejas |
| Stubs sin fprintf | ✅ Aplicado | reduce overhead de CPU |
| Symlinks de texturas | ✅ Aplicado | resuelve assets faltantes |
| TLG_DMEM_MB=4608 | ✅ Configurado | retail, sin overhead de devkit |
| Shader cache | ✅ Activo | evita recompilar shaders entre ejecuciones |
| Write-merge (tlggpu_cpu_write) | ✅ Activo (weak stub retorna 0) | merge de escrituras pequeñas |

## Lo que nos falta (de los otros ports)

### Fase 1 — PGO (mayor impacto, sin cambios de código) [+10-20% CPU]

Profile-Guided Optimization: recolectar perfil real de ejecución y recompilar.

```bash
# Paso 1: recolectar perfil (jugar 3-5 min en áreas variadas)
TLG_PGO=generate TLG_DMEM_MB=4608 TLG_GAME_DIR="..." bash run.sh
# Paso 2: recompilar con perfil
TLG_PGO=use bash build.sh
# Paso 3: verificar mejora
TLG_DMEM_MB=4608 TLG_GAME_DIR="..." bash run.sh
```

**Estado:** perfil recolectado (201 gcda files, ~4 min de juego). Falta recompilar con PGO=use y verificar.

**Nota:** el perfil se recolectó en la 1.00 (que funciona). El PGO optimiza los hot paths reales.

### Fase 2 — Refinar stubs del hot path [+5-15% CPU]

Los 81 stubs con firma genérica `int name(void)` causan:
- Mismatch de calling convention (el juego pasa args, el stub los ignora)
- Overhead de función call + return 0
- Potencial undefined behavior

**Acción:**
1. Ejecutar con `TLG_VERBOSE_LOG=2` y capturar log.
2. Identificar stubs más llamados: `grep "TLOU stub" logs/*.log | sort | uniq -c | sort -rn | head -20`
3. Refinar firma de los top 10 (usar Ghidra para obtener firma real de la función en el eboot).
4. Reemplazar `tlou_stub()` (que retorna 0) por implementación correcta o no-op inline.

**Stubs más probables en hot path:**
- `sceGnm*` (GPU commands) — si están en stubs
- `sceKernel*` (memory, threads) — si están en stubs
- `scePad*` — input (ya resuelto, 7 de 8)
- `sceAudioOut*` — audio (ya resuelto)

### Fase 3 — Parallel GPU (draw preparation on workers) [+5-11% FPS]

Basado en `parallel_gpu.md` de SpartanPort/ps4_core. Mueve la preparación de draws a workers.

**Pasos (de SpartanPort):**
1. **Speculative draw preparation on workers:** workers replay command buffers y precomputan pipeline keys, texture descriptions, etc. GPU thread valida y usa solo si match.
2. **Thread-safe cache lookups:** buffers/images/views lookup en workers, creación en GPU thread.
3. **Parallel Vulkan recording:** cada worker graba su propio command buffer.

**Prerequisito:** refactor de sharp consumers (leer user data via view, no shared members).

**Impacto:** +11.5% en SpartanPort (4 workers, 98% draws preparados).

**Estado en TLOU:** no implementado. Requiere modificar shadPS4.

### Fase 4 — Guest write fault optimization [+22% FPS en streaming]

Basado en `parallel_gpu.md`. El juego escribe en páginas protegidas (GPU tracking), causando faults.

**Pasos:**
1. **64 KiB unprotect window** (`TLG_FAULT_WINDOW`): en vez de desproteger 4 KiB, desproteger 64 KiB. Reduce faults de 115k/s a 16k/s. +22% FPS en streaming.
2. **Userfaultfd** (`TLG_UFFD=1`): tracking de escrituras via userfaultfd en vez de mprotect. Sin address-space write lock.
3. **File reads en páginas protegidas:** tocar cada página destino antes de leer.

**Impacto:** +22% FPS en áreas de streaming (carga de niveles).

**Estado en TLOU:** no implementado. Requiere modificar runtime_memory.c.

### Fase 5 — Texture description cache [+43% FPS en escenas con texturas]

Basado en `parallel_gpu.md`. Cache de descripciones de texturas para evitar lookups repetidos.

**Pasos:**
1. Cache 2-way/4096 de texture descriptions.
2. Same-target fast path.
3. LRU touch skip.
4. No per-texture meta lookup.

**Impacto:** +43% FPS en escenas con texturas (93.9 vs 65.6 FPS en SpartanPort).

**Estado en TLOU:** no implementado. Requiere modificar shadPS4.

### Fase 6 — Copy threads y staging pool [+25% FPS]

Basado en `parallel_gpu.md`. Copias de guest a staging en paralelo.

**Pasos:**
1. **Copy threads** (`TlgCopy::Async`): copias en hilos separados, batched per thread (~512 KiB por wakeup).
2. **Staging pool**: mantener 512 MiB (`TLG_STAGING_KEEP_MB`), liberar resto después de 30s.
3. **Populate 128 MiB at startup**: evitar kernel allocation en el primer frame.
4. **Guest-visible fences**: esperar copias antes de submission.

**Impacto:** +25% FPS en streaming.

**Estado en TLOU:** no implementado. Requiere modificar runtime_memory.c y shadPS4.

### Fase 7 — Motion vectors y depth-adaptive TAA (calidad)

Basado en `motion_vectors.md` y `DEPTH_ADAPTIVE_TAA.md`.

**Pasos:**
1. **Motion vectors:** computar vectores de movimiento para FSR temporal. Solo para shaders con buffer de pose/huesos (1024-16384 bytes).
2. **Depth-adaptive TAA:** TAA nativo que usa motion vectors para reducir ghosting.
3. **Object motion:** vectores de movimiento de objetos (personajes, armas).

**Impacto:** calidad de imagen (menos ghosting, mejor TAA). No FPS directo.

**Estado en TLOU:** no implementado. Requiere modificar shadPS4.

### Fase 8 — Refinar stubs restantes (estabilidad + rendimiento)

1. Implementar los 81 stubs con firmas reales (usar Ghidra).
2. Resolver los 37 NIDs sin nombre (NID DB / RE).
3. Promover borrowables genéricos a ps4_core.
4. Añadir stubs inline (no-op sin function call overhead).

**Impacto:** estabilidad + rendimiento. **Tiempo:** semanas.

## Orden de implementación (por impacto/tiempo)

| Prioridad | Fase | Impacto | Tiempo | Dificultad |
|---|---|---|---|---|
| 1 | PGO (recompilar con perfil) | +10-20% | 10 min | Fácil |
| 2 | Refinar stubs hot path | +5-15% | 1-2 h | Media |
| 3 | Guest write fault optimization | +22% (streaming) | 2-4 h | Media |
| 4 | Copy threads + staging pool | +25% (streaming) | 2-4 h | Media |
| 5 | Texture description cache | +43% (texturas) | 2-4 h | Media |
| 6 | Parallel GPU (draw prep) | +11.5% | 1-2 semanas | Alta |
| 7 | Motion vectors + TAA | calidad | 1-2 semanas | Alta |
| 8 | Refinar todos los stubs | estabilidad | semanas | Alta |

## Métricas de éxito

| Métrica | Baseline | Objetivo (Fase 1-4) | Objetivo (Fase 5-8) |
|---|---|---|---|
| FPS (native res) | ~19-20 | 30+ | 40-60 |
| Frame time | ~50 ms | <33 ms | <25 ms |
| Memory ops/sec | ~200K | <150K | <100K |
| Mutex locks/frame | ~60 | <30 | <20 |

## Lo que NO haremos (trucos)

- ❌ Bajar resolución (FSR, 720p) — el usuario no quiere
- ❌ Limitar RAM a menos de lo disponible
- ❌ Desactivar features del juego
- ❌ Usar software rendering

## Comandos rápidos

```bash
# PGO generate (ya recolectado, recompilar)
TLG_PGO=use bash build.sh

# PGO generate (nuevo perfil)
TLG_PGO=generate TLG_DMEM_MB=4608 TLG_GAME_DIR="..." bash run.sh

# Verificar stubs más llamados
grep "TLOU stub" logs/*.log | sed 's/.*\[TLOU stub\] //' | sort | uniq -c | sort -rn | head -20

# Build con flags optimizados
export CC=gcc-14 CXX=g++-14
bash build.sh
```
EOF
echo "Plan V2 creado"