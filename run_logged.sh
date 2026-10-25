#!/usr/bin/env bash
# run_logged.sh — ejecuta el port capturando todo el output a un log con timestamp.
set -euo pipefail
cd -- "$(dirname -- "$0")"
LOGDIR="${TLG_LOG_DIR:-./logs}"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/tlou_$(date +%Y%m%d_%H%M%S).log"
echo "Log: $LOGFILE"
# TLOU treats any direct-memory size != 4608 MiB as a devkit. Force retail value.
TLG_PREBUILT="${TLG_PREBUILT:-1}" \
TLG_PROBE="${TLG_PROBE:-out/tlg-probe}" \
TLG_DMEM_MB="${TLG_DMEM_MB:-4608}" \
TLG_VERBOSE_LOG="${TLG_VERBOSE_LOG:-1}" \
TLG_GAME_DIR="${TLG_GAME_DIR:-./CUSA00552}" \
TLG_WRITE_MERGE="${TLG_WRITE_MERGE:-1}" \
TLG_FAULT_WINDOW="${TLG_FAULT_WINDOW:-256}" \
TLG_COPY_THREADS="${TLG_COPY_THREADS:-6}" \
TLG_STAGING_KEEP_MB="${TLG_STAGING_KEEP_MB:-512}" \
TLG_ASYNC_FENCES="${TLG_ASYNC_FENCES:-1}" \
TLG_DEFERRED_READBACK="${TLG_DEFERRED_READBACK:-1}" \
TLG_STALE_READBACK="${TLG_STALE_READBACK:-1}" \
TLG_HOT_PAGES="${TLG_HOT_PAGES:-1}" \
TLG_PHYS_CORES="${TLG_PHYS_CORES:-6}" \
TLG_READBACKS="${TLG_READBACKS:-2}" \
TLG_READBACK_LINEAR="${TLG_READBACK_LINEAR:-1}" \
TLG_UPSCALER="${TLG_UPSCALER:-off}" \
    bash run.sh "$@" 2>&1 | tee "$LOGFILE"
echo ""
echo "Log guardado en: $LOGFILE"
