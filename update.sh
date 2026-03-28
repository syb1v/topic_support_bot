#!/usr/bin/env bash
# ===========================================
# Topic Support Bot — Автообновление
# Использование: bash update.sh [branch]
# ===========================================
set -euo pipefail

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BRANCH="${1:-main}"

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${CYAN}[→]${NC} $1"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Topic Support Bot — Обновление       ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 1. Переход в директорию
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
log "Рабочая директория: $PROJECT_DIR"

# 2. Обновление кода из Git
info "Получение последних изменений из Git ($BRANCH)..."
git fetch origin "$BRANCH" || warn "Не удалось выполнить fetch"
git reset --hard origin/"$BRANCH" || err "Не удалось сбросить изменения к origin/$BRANCH"
git pull origin "$BRANCH" || err "Не удалось выполнить pull"
log "Код успешно обновлен"

# 3. Пересборка и перезапуск Docker
info "Сборка Docker образов..."
docker compose build --parallel || err "Ошибка при сборке образов"
log "Образы собраны"

info "Перезапуск контейнеров..."
docker compose up -d --remove-orphans || err "Ошибка при запуске контейнеров"
log "Контейнеры запущены"

# 4. Очистка старых образов
info "Очистка неиспользуемых данных Docker..."
docker image prune -f > /dev/null || true
log "Система очищена"

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Бот успешно обновлен!            ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
docker compose ps