#!/usr/bin/env bash
# ==============================================================================
# PHASE 30: TELEMETRY WATCHDOG LAYER FOR JARVIS UNIVERSAL
# ==============================================================================
# Objective: Monitor the detached production container logs, track scene checkpoint
# validation milestones, and trap any unhandled exceptions in the local environment.

CONTAINER_NAME="jarvis_production_render"

clear
echo "======================================================================"
echo "[*] JARVIS UNIVERSAL: PRODUCTION TELEMETRY MONITOR ACTIVATED"
echo "[-] Target Context: 'Chronological Arbitrage: The 1980 Playbook'"
echo "======================================================================"

# Verify container is actively running on the local host architecture
if [ ! "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "[-] Warning: ${CONTAINER_NAME} is not actively running."
    echo "[*] Scanning for recently exited initialization layers..."
    docker ps -a -f name=${CONTAINER_NAME} --format "Status: {{.Status}}"
    exit 1
fi

echo "[+] Active container connection verified. Streaming pipeline updates..."
echo "----------------------------------------------------------------------"

# Stream logs, highlighting key scene transitions and checkpoint events
docker logs -f "${CONTAINER_NAME}" | grep -E --line-buffered \
    "\[\*\]|\[\+\]|\[\!\]|Error|Exception|Checkpoint|Reel|Processing Scene|KSampler"
