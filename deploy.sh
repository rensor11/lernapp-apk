#!/bin/bash
# Deploy-Script für die Lernapp auf dem Debian-Server
# Wird auf dem DEBIAN-SERVER ausgeführt, NICHT auf Windows!

set -e

DEPLOY_DIR="/opt/lernapp"

echo "=== Lernapp Deploy ==="

# Alte DB löschen (wird automatisch neu erstellt)
echo "Lösche alte Datenbank..."
rm -f "$DEPLOY_DIR/lernapp.db"

# Server stoppen
echo "Stoppe alten Server..."
pkill -f "python.*server_neu.py" 2>/dev/null || true
sleep 2

# Server neu starten
echo "Starte Server neu..."
cd "$DEPLOY_DIR"
nohup python3 server_neu.py > /tmp/lernapp.log 2>&1 &
sleep 3

# Testen
echo "Teste API..."
HEALTH=$(curl -s http://localhost:5000/api/health 2>/dev/null)
echo "Health: $HEALTH"

REG=$(curl -s -X POST http://localhost:5000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testdeploy","password":"test123456"}' 2>/dev/null)
echo "Register-Test: $REG"

echo ""
echo "=== Deploy fertig! ==="
echo "Log: tail -f /tmp/lernapp.log"
