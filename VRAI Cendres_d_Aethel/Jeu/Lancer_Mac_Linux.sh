#!/bin/sh
cd "$(dirname "$0")" || exit 1
echo "CENDRES D'AETHEL"
echo "1. Edition Ultra Hard (options ajoutees)"
echo "2. Edition Monde ouvert"
printf "Choisis une edition (1-2) : "
read choix || exit 1
if [ ! -x ".venv/bin/python" ]; then
  echo "Creation de l'environnement Python local..."
  python3 -m venv .venv || {
    echo "Impossible de creer l'environnement virtuel. Sur Ubuntu/Debian, execute :"
    echo "  sudo apt update && sudo apt install python3-venv python3-full"
    exit 1
  }
fi
.venv/bin/python -m pip install --upgrade pip || exit 1
.venv/bin/python -m pip install -r requirements.txt || exit 1
case "$choix" in
  1) exec .venv/bin/python cendres_d_aethel.py ;;
  2) exec .venv/bin/python cendres_d_aethel_monde_ouvert.py ;;
  *) echo "Choix invalide."; exit 1 ;;
esac
