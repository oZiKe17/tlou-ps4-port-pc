# PGO (Profile-Guided Optimization) — TLOU Port

## Paso 1: Recolectar perfil (jugar 2-5 minutos)
```bash
rm -rf pgo && mkdir pgo
TLG_PGO=generate TLG_DMEM_MB=4608 TLG_GAME_DIR="..." bash run.sh
# Juega 2-5 minutos (menús, gameplay, cinemáticas)
# Luego cierra el juego (Ctrl+C o salir)
```

## Paso 2: Recompilar con el perfil
```bash
TLG_PGO=use bash build.sh
```

## Paso 3: Verificar mejora
```bash
TLG_DMEM_MB=4608 TLG_GAME_DIR="..." bash run.sh
# Comparar FPS con el anterior
```

## Notas
- PGO típicamente da 10-20% de mejora en CPU.
- El perfil se guarda en `port/pgo/` (archivos .gcda).
- Si cambias mucho el código, re-recolecta el perfil.
- `TLG_PGO=off` desactiva PGO (build más rápido para debug).
