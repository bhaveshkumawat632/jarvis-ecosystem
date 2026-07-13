#!/usr/bin/env bash
# run_docker_production.sh (Updated for Phase 34)

echo "[*] Spinning up Jarvis Universal Asynchronous Infrastructure..."

# Tear down any existing stale infrastructure
docker-compose down

# Rebuild the unified image and launch the background daemon network
docker-compose up --build -d

echo "[+] Asynchronous Pipeline Activated. Monitoring Orchestrator Output..."
# Attach to the master node to track the pipeline's progress
docker logs -f jarvis_orchestrator
