#!/usr/bin/env bash
# ===========================================
# Topic Support Bot — Автоматический деплой
# Использование: bash deploy.sh
# ===========================================
set -euo pipefail

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${CYAN}[→]${NC} $1"; }

echo ""
echo -e "${CYAN}╔══════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║     Topic Support Bot — Деплой           ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════╝${NC}"
echo ""

# 1. Проверка root
if [ "$EUID" -ne 0 ] && [ "$EUID" -ne $(id -u) ]; then
    warn "Желательно запускать от root или иметь права на Docker"
fi

# 2. Определяем директорию проекта
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"
log "Директория проекта: $PROJECT_DIR"

# 3. Установка Docker (если нет)
if command -v docker &> /dev/null; then
    log "Docker уже установлен: $(docker --version | head -1)"
else
    info "Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    log "Docker установлен"
fi

# 4. Проверка .env
if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        info "Создание .env из .env.example..."
        cp .env.example .env
        warn "Отредактируйте .env и добавьте BOT_TOKEN!"
    else
        err "Файл .env не найден! Создайте его."
    fi
fi

# 5. Остановка старых контейнеров
info "Остановка старых контейнеров..."
docker compose down --remove-orphans 2>/dev/null || true

# 6. Сборка и запуск
info "Сборка Docker-образа..."
docker compose build
log "Сборка завершена"

info "Запуск бота..."
docker compose up -d
log "Контейнеры запущены"

# 7. Проверка логов
info "Проверка статуса..."
sleep 2
docker compose ps

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║         Бот успешно запущен!             ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
echo ""
info "Используйте 'docker compose logs -f' для просмотра логов."
