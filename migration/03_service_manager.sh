#!/bin/bash
###############################################################################
# 03_service_manager.sh
# Steuert alle LernApp-Dienste: start, stop, status, restart, logs
# Ausfuehren als root:  bash 03_service_manager.sh [start|stop|status|restart|logs]
###############################################################################
set -euo pipefail

# --- Alle verwalteten Dienste in Start-Reihenfolge ---
SERVICES=(
  "sshd"
  "lernapp-flask"
  "cloudflared-tunnel"
  # "lernapp-node"  # einkommentieren wenn Node.js genutzt wird
)

ACTION="${1:-status}"

usage() {
  echo "Benutzung: $0 {start|stop|restart|status|logs}"
  echo ""
  echo "  start   - Startet alle Dienste in der richtigen Reihenfolge"
  echo "  stop    - Stoppt alle Dienste (umgekehrte Reihenfolge)"
  echo "  restart - Neustart aller Dienste"
  echo "  status  - Zeigt Status aller Dienste"
  echo "  logs    - Zeigt aktuelle Logs aller Dienste"
  exit 1
}

start_all() {
  echo "=== Starte alle Dienste ==="
  for svc in "${SERVICES[@]}"; do
    echo -n "  Starte $svc... "
    systemctl start "$svc" 2>/dev/null && echo "OK" || echo "FEHLER"
  done
  echo "=== Alle Dienste gestartet ==="
}

stop_all() {
  echo "=== Stoppe alle Dienste ==="
  # Umgekehrte Reihenfolge: zuerst Cloudflared, dann Flask, SSH bleibt
  for (( i=${#SERVICES[@]}-1; i>=0; i-- )); do
    svc="${SERVICES[$i]}"
    # SSH nicht stoppen (sonst sperren wir uns aus)
    if [ "$svc" = "sshd" ]; then
      echo "  $svc wird uebersprungen (SSH darf nicht gestoppt werden)"
      continue
    fi
    echo -n "  Stoppe $svc... "
    systemctl stop "$svc" 2>/dev/null && echo "OK" || echo "FEHLER"
  done
  echo "=== Dienste gestoppt ==="
}

restart_all() {
  stop_all
  echo ""
  start_all
}

status_all() {
  echo "=========================================="
  echo " LernApp Server - Dienste-Status"
  echo "=========================================="
  for svc in "${SERVICES[@]}"; do
    STATUS=$(systemctl is-active "$svc" 2>/dev/null || echo "inaktiv")
    ENABLED=$(systemctl is-enabled "$svc" 2>/dev/null || echo "deaktiviert")
    printf "  %-25s  Aktiv: %-10s  Autostart: %s\n" "$svc" "$STATUS" "$ENABLED"
  done
  echo "=========================================="
  echo ""
  echo "Systemressourcen:"
  echo "  CPU-Last:    $(cat /proc/loadavg | cut -d' ' -f1-3)"
  echo "  RAM:         $(free -h | awk '/^Mem:/{print $3 "/" $2}')"
  echo "  Festplatte:  $(df -h / | awk 'NR==2{print $3 "/" $2 " (" $5 " belegt)"}')"
  echo "=========================================="
}

show_logs() {
  echo "=== Letzte Logs (alle Dienste, letzte 50 Zeilen) ==="
  for svc in "${SERVICES[@]}"; do
    echo ""
    echo "--- $svc ---"
    journalctl -u "$svc" --no-pager -n 15 2>/dev/null || echo "  Keine Logs verfuegbar."
  done
}

case "$ACTION" in
  start)   start_all   ;;
  stop)    stop_all     ;;
  restart) restart_all  ;;
  status)  status_all   ;;
  logs)    show_logs    ;;
  *)       usage        ;;
esac
