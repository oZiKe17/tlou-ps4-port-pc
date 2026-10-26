#!/usr/bin/env bash
# run_logged.sh — ejecuta el port capturando todo el output a un log con timestamp.
# Uso: bash run_logged.sh [args extra para run.sh]
set -euo pipefail
cd -- "$(dirname -- "$0")/port"
LOGDIR="${TLG_LOG_DIR:-${TLG_DATA_DIR:-$HOME/.local/share/tlou-pc}/logs}"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/tlou_$(date +%Y%m%d_%H%M%S).log"
echo "Log: $LOGFILE"
echo "Verbose: ${TLG_VERBOSE_LOG:-0}"
# TLG_VERBOSE_LOG=2 para detalle máximo
# TLOU treats any direct-memory size != 4608 MiB as a devkit and allocates a
# debug arena that does not fit. Force the retail value unless overridden.
# TLG_PREBUILT=1: skip the (slow) GPU rebuild, use the already-built binary.
# Debug traces are opt-in: serializing them to the log adds I/O and work to hot paths.
# Copy-worker and staging budgets use automatic, per-machine sizing unless explicitly set.
# Hot pages stay off by default; the recorded scene regressed to 33 FPS and hit a GPU ring timeout.
prebuilt=${TLG_PREBUILT:-}
if [[ -z $prebuilt && -x out/tlg-probe && -f out/gpu/libtlggpu.so ]]; then
    stale=0
    for artifact in out/tlg-probe out/gpu/libtlggpu.so; do
        if [[ build.sh -nt $artifact ]] || \
           find src gpu third_party/LibAtrac9 -name .git -prune -o -type f -newer "$artifact" -print -quit | grep -q .; then
            stale=1
            break
        fi
    done
    if (( stale )); then
        echo 'Port sources changed; rebuilding before launch.'
    else
        prebuilt=1
    fi
fi
TLG_PREBUILT="$prebuilt" \
TLG_PROBE="${TLG_PROBE:-out/tlg-probe}" \
TLG_DMEM_MB="${TLG_DMEM_MB:-4608}" \
TLG_VERBOSE_LOG="${TLG_VERBOSE_LOG:-0}" \
TLG_LANGUAGE="${TLG_LANGUAGE:-20}" \
TLG_DATA_DIR="${TLG_DATA_DIR:-$HOME/.local/share/tlou-pc}" \
TLG_GAME_DIR="${TLG_GAME_DIR:-../CUSA00552}" \
TLG_WRITE_MERGE="${TLG_WRITE_MERGE:-1}" \
TLG_WRITE_MERGE_MIN="${TLG_WRITE_MERGE_MIN:-4096}" \
TLG_FAULT_WINDOW="${TLG_FAULT_WINDOW:-256}" \
TLG_ASYNC_FENCES="${TLG_ASYNC_FENCES:-1}" \
TLG_DEFERRED_READBACK="${TLG_DEFERRED_READBACK:-1}" \
TLG_STALE_READBACK="${TLG_STALE_READBACK:-1}" \
TLG_HOT_PAGES="${TLG_HOT_PAGES:-0}" \
TLG_READBACKS="${TLG_READBACKS:-2}" \
TLG_READBACK_LINEAR="${TLG_READBACK_LINEAR:-1}" \
    bash run.sh "$@" 2>&1 | tee "$LOGFILE"
echo ""
echo "Log guardado en: $LOGFILE"
echo "Para ver resumen final: tail -40 $LOGFILE"
