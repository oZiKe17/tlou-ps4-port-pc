#!/usr/bin/env bash
# Adds "The Last Guardian" to the applications menu, pointing at this folder (--remove undoes it).
set -euo pipefail
here=$(cd -- "$(dirname -- "$0")" && pwd)
apps=${XDG_DATA_HOME:-$HOME/.local/share}/applications
entry=$apps/tlg-pc.desktop
if [[ ${1:-} == --remove ]]; then
    rm -f "$entry"; echo "Removed $entry"; exit 0
fi
mkdir -p "$apps"
cat > "$entry" <<DESKTOP
[Desktop Entry]
Type=Application
Name=The Last Guardian
Comment=The Last Guardian (PC port)
Exec="$here/The Last Guardian"
Path=$here
Icon=$here/launcher/tlg.png
Terminal=false
Categories=Game;
StartupWMClass=tlg-pc
DESKTOP
echo "Installed $entry"
