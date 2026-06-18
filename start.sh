#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
#  start.sh  —  MLOps E-Commerce Pipeline Startup Script
#  Starts all services: Redis, MariaDB, MLflow, FastAPI, Airflow
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Colours ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Colour

# ── Helpers ───────────────────────────────────────────────────────────────────
log()     { echo -e "${CYAN}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }

banner() {
  echo -e "${BOLD}${CYAN}"
  echo "  ╔══════════════════════════════════════════════════╗"
  echo "  ║       MLOps E-Commerce Pipeline Launcher         ║"
  echo "  ║   Redis · MariaDB · MLflow · FastAPI · Airflow   ║"
  echo "  ╚══════════════════════════════════════════════════╝"
  echo -e "${NC}"
}

# ── Pre-flight checks ─────────────────────────────────────────────────────────
check_dependencies() {
  log "Checking dependencies..."

  if ! command -v docker &>/dev/null; then
    error "Docker is not installed or not in PATH. Please install Docker."
    exit 1
  fi

  if ! docker compose version &>/dev/null 2>&1 && ! docker-compose version &>/dev/null 2>&1; then
    error "Docker Compose not found. Please install Docker Compose."
    exit 1
  fi

  if ! docker info &>/dev/null 2>&1; then
    error "Docker daemon is not running. Please start Docker."
    exit 1
  fi

  success "All dependencies satisfied."
}

# ── Determine compose command ─────────────────────────────────────────────────
get_compose_cmd() {
  if docker compose version &>/dev/null 2>&1; then
    echo "docker compose"
  else
    echo "docker-compose"
  fi
}

COMPOSE=$(get_compose_cmd)

# ── Wait for a service health ─────────────────────────────────────────────────
wait_healthy() {
  local container="$1"
  local max_wait="${2:-60}"
  local elapsed=0

  log "Waiting for ${BOLD}${container}${NC} to be healthy..."
  while [ $elapsed -lt $max_wait ]; do
    status=$(docker inspect --format='{{.State.Health.Status}}' "$container" 2>/dev/null || echo "missing")
    if [ "$status" = "healthy" ]; then
      success "${container} is healthy."
      return 0
    fi
    sleep 3
    elapsed=$((elapsed + 3))
  done

  error "${container} did not become healthy within ${max_wait}s."
  return 1
}

# ── Main ──────────────────────────────────────────────────────────────────────
main() {
  banner
  check_dependencies

  # ── Step 1: Build images ───────────────────────────────────────────────────
  log "Building Docker images (FastAPI)..."
  $COMPOSE build --quiet
  success "Images built."

  # ── Step 2: Start infrastructure (Redis + MariaDB) ────────────────────────
  log "Starting infrastructure services: Redis & MariaDB..."
  $COMPOSE up -d redis mariadb
  wait_healthy "mlops_redis"   60
  wait_healthy "mlops_mariadb" 90

  # ── Step 3: Start MLflow ──────────────────────────────────────────────────
  log "Starting MLflow tracking server..."
  $COMPOSE up -d mlflow
  sleep 5
  success "MLflow started  →  http://localhost:5002"

  # ── Step 4: Start FastAPI ─────────────────────────────────────────────────
  log "Starting FastAPI inference server..."
  $COMPOSE up -d web
  sleep 5
  success "FastAPI started  →  http://localhost:8005"

  # ── Step 5: Start Airflow ─────────────────────────────────────────────────
  log "Starting Apache Airflow..."
  $COMPOSE up -d airflow
  sleep 10
  success "Airflow started  →  http://localhost:8081"

  # ── Step 6: Summary ───────────────────────────────────────────────────────
  echo ""
  echo -e "${BOLD}${GREEN}  ✅ All services are up!${NC}"
  echo -e "${BOLD}  ─────────────────────────────────────────────────${NC}"
  echo -e "  ${CYAN}FastAPI   ${NC}→  http://localhost:8005"
  echo -e "  ${CYAN}FastAPI Docs${NC}→  http://localhost:8005/docs"
  echo -e "  ${CYAN}Airflow   ${NC}→  http://localhost:8081  (admin / admin)"
  echo -e "  ${CYAN}MLflow    ${NC}→  http://localhost:5002"
  echo -e "  ${CYAN}MariaDB   ${NC}→  localhost:3310  (mlops_user / mlops_password)"
  echo -e "  ${CYAN}Redis     ${NC}→  localhost:6380"
  echo -e "${BOLD}  ─────────────────────────────────────────────────${NC}"
  echo ""
  log "To stop all services run:  ${BOLD}./stop.sh${NC}  or  ${BOLD}docker compose down${NC}"
}

main "$@"
