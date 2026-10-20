#!/bin/sh
set -eu
HERE="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
SRC="$HERE/Jeu"
DEST="$HOME/.local/share/cendres-daethel"
APPS="$HOME/.local/share/applications"
mkdir -p "$DEST" "$APPS"
cp -R "$SRC"/. "$DEST"/
chmod +x "$DEST/Lancer_Mac_Linux.sh"
cat > "$DEST/Lancer_Cendres_Aethel.sh" <<'EOF'
#!/bin/sh
cd "$HOME/.local/share/cendres-daethel" || exit 1
exec ./Lancer_Mac_Linux.sh
EOF
chmod +x "$DEST/Lancer_Cendres_Aethel.sh"
cat > "$APPS/cendres-daethel.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Cendres d'Aethel
Comment=Lancer Cendres d'Aethel
Exec=$DEST/Lancer_Cendres_Aethel.sh
Path=$DEST
Terminal=true
Categories=Game;
EOF
chmod +x "$APPS/cendres-daethel.desktop"
# Ajouter un raccourci sur le bureau si le dossier existe
DESKTOP_DIR="$(xdg-user-dir DESKTOP 2>/dev/null || printf '%s' "$HOME/Desktop")"
if [ -d "$DESKTOP_DIR" ]; then
  cp "$APPS/cendres-daethel.desktop" "$DESKTOP_DIR/Cendres d'Aethel.desktop"
  chmod +x "$DESKTOP_DIR/Cendres d'Aethel.desktop"
fi
printf '
Installation terminée. Lance « Cendres d’Aethel » depuis le menu Applications.
'
printf 'Si Ubuntu/Debian demande des prérequis : sudo apt install python3-venv python3-full
'
