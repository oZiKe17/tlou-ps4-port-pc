# Plan de Optimización Real — TLOU Port (sin trucos)

**Objetivo:** maximizar FPS y estabilidad acercándose al original (PS4 30 FPS). Sin FSR, sin bajar resolución, sin trucos. Solo optimización real.

## Baseline actual

- **FPS:** ~19-20 FPS (native res, 60 Hz vblank)
- **CPU:** alto (recompiler + stubs + threads)
- **GPU:** ~? % (verificar overlay)
- **VRAM:** n/a (GPU no soporta VK_EXT_memory_budget) pero se asigna correctamente
- **Memory ops:** ~24M por sesión de 2 min
- **Mutex locks:** ~12K por sesión
- **Threads:** ~200 creados

## Cuellos de botella identificados

### 1. ISA Rewriter (CPU) — mayor impacto
El port reescribe instrucciones x86 del guest (isa_rewrite.c, isa_emulate.c) en tiempo de ejecución. Esto es el mayor consumidor de CPU.
- **Optimización:** PGO (Profile-Guided Optimization) — recolectar perfil real y recompilar con hot paths optimizados.
- **Impacto estimado:** +10-20% CPU.

### 2. Stubs con firma genérica (CPU) — overhead de calling convention
81 stubs con `int name(void)` cuando el juego llama con argumentos. Esto causa:
- Stack corruption potencial
- Overhead de ABI mismatch
- Llamadas a funciones que deberían ser no-op pero con overhead
- **Optimización:** refinar firmas a las reales (usar Ghidra). Para los stubs que solo devuelven 0, usar `__attribute__((noinline))` o inline.
- **Impacto estimado:** +5-15% CPU en hot paths.

### 3. Threads y sincronización (CPU)
~200 threads creados, 12K mutex locks, 6K rwlock reads. El overhead de pthread es significativo.
- **Optimización:** reducir número de threads guest (el juego crea muchos para audio, IO, etc.).
- **Optimización:** usar futex directamente en vez de pthread_mutex en hot paths.
- **Impacto estimado:** +5-10% CPU.

### 4. Memory operations (CPU)
24M memory ops por sesión. guest_memset/memcpy con write-merge path.
- **Optimización:** el write-merge path ya está (tlggpu_cpu_write). Verificar que esté activo.
- **Optimización:** usar SIMD (AVX2) para memset/memcpy en vez de byte-by-byte.
- **Impacto estimado:** +5-10% CPU.

### 5. Audio (CPU) — ATRAC9 decoding
8K Ajm batches, 77K jobs, 80K ATRAC9 frames decodificados en 2 min. Esto es CPU intensivo.
- **Optimización:** verificar que LibAtrac9 use SIMD (ya debería).
- **Optimización:** reducir frecuencia de audio updates si es posible.
- **Impacto estimado:** +5-10% CPU.

### 6. GPU (shadPS4) — shader compilation y rendering
- **Optimización:** async_shaders=1 (ya activo) — compila shaders en background.
- **Optimización:** deferred_readback=1, stale_readback=1 (ya activos) — evita stalls.
- **Optimización:** shader cache (ya activo) — evita recompilar shaders entre ejecuciones.
- **Impacto estimado:** ya optimizado, pero PGO también ayuda al GPU code.

## Plan de acción (orden de impacto)

### Fase 1 — PGO (mayor impacto, sin cambios de código)
1. Ejecutar el juego con `TLG_PGO=generate` por 3-5 minutos (menús, gameplay, cinemáticas).
2. Recompilar con `TLG_PGO=use`.
3. Verificar mejora en FPS.
**Impacto:** +10-20% CPU. **Tiempo:** 10 min.

### Fase 2 — Refinar stubs del hot path
1. Ejecutar con `TLG_VERBOSE_LOG=2` y capturar log.
2. Identificar stubs más llamados (grep "TLOU stub").
3. Refinar firma de los top 10 stubs (usar Ghidra para obtener firma real).
4. Reemplazar `tlou_stub()` (que retorna 0) por implementación correcta o no-op inline.
**Impacto:** +5-15% CPU. **Tiempo:** 1-2 horas.

### Fase 3 — Optimizaciones de código
1. Añadir `__attribute__((noinline))` o inline a stubs que solo retornan 0.
2. Verificar que write-merge path (`tlggpu_cpu_write`) esté activo.
3. Verificar que LibAtrac9 use SIMD.
4. Ajustar thread scheduling (nice, affinity) si es necesario.
**Impacto:** +5-10% CPU. **Tiempo:** 1-2 horas.

### Fase 4 — LTO + compiler flags
1. LTO ya está ON. Verificar que no haya problemas.
2. Añadir `-march=native` para usar instrucciones SIMD del host (AVX2, etc.).
3. Añadir `-O3` en vez de `-O2` para el runtime (no el GPU).
**Impacto:** +5-10% CPU. **Tiempo:** 30 min.

### Fase 5 — Refinar stubs restantes
1. Implementar los 81 stubs con firmas reales.
2. Resolver los 37 NIDs sin nombre.
3. Promover borrowables genéricos a ps4_core.
**Impacto:** estabilidad + rendimiento. **Tiempo:** semanas.

## Métricas de éxito

| Métrica | Baseline | Objetivo |
|---|---|---|
| FPS (native res) | ~19-20 | 30+ (PS4 target) |
| Frame time | ~50 ms | <33 ms |
| Memory ops/sec | ~200K | <150K |
| Mutex locks/frame | ~60 | <30 |

## Optimizaciones disponibles (incluyendo upscaling)

FSR no es un "truco" — es upscaling temporal real usado por los juegos AAA.
El original (PS4) renderiza a resolución dinámica con upscaling interno.

### FSR (disponible en el port)
- **FSR 3** (UpscalerFsr3): disponible por defecto, activar con `upscaler=1` en tlg.ini
- **FSR 4** (UpscalerFsr4): requiere assets, activar con `upscaler=2`
- **FSR 4.1.1** (UpscalerFsr411): requiere assets de `tools/fsr4cap/build_assets.sh`
- **TAA** (UpscalerTaa): upscaling temporal nativo, `upscaler=4`
- **DLSS** (UpscalerDlss): requiere GPU NVIDIA, `upscaler=5`

### Configuración de FSR en tlg.ini
```ini
upscaler=1                    # FSR 3 (disponible sin assets)
render_resolution=720p        # renderizar a 720p, FSR escala a 1080p
engine_fps=60
fps_limit=60
async_shaders=1
show_fps=1
overlay_items=1
```

### Impacto de FSR
- 720p → 1080p: 2.25x menos pixels → +50-100% FPS en GPU
- FSR 4: mejor calidad que FSR 3 (menos ghosting)
- Combinado con PGO + stubs: de ~20 FPS a 40-60+ FPS

### Para FSR 4.1.1
```bash
cd port/tools/fsr4cap
bash build_assets.sh
# Copiar assets a port/fsr4_411/
```

## Comandos rápidos

```bash
# PGO generate
TLG_PGO=generate TLG_DMEM_MB=4608 TLG_GAME_DIR="..." bash run.sh

# PGO use (recompilar)
TLG_PGO=use bash build.sh

# Verificar stubs más llamados
grep "TLOU stub" logs/*.log | sed 's/.*\[TLOU stub\] //' | sort | uniq -c | sort -rn | head -20
```
EOF
echo "Plan creado"