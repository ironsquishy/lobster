# =========================
# Lobster Makefile
# =========================

# -------- Env loading --------
ENV_FILE ?= .env

ifneq (,$(wildcard $(ENV_FILE)))
include $(ENV_FILE)
export
endif

# -------- Config --------
PROJECT_NAME := lobster
APP_MODULE := app.main:app
PORT ?= 4000

VENV := .venv
PYTHON := python3
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn

DOCKER_IMAGE := lobster-local
DOCKER_CONTAINER := lobster-dev

DATA_DIR := $(PWD)/data

# Pull from .env
API_KEY ?= $(LOBSTER_API_KEY)
BASE_URL ?= http://127.0.0.1:$(PORT)

# fallback if not set
API_KEY := $(or $(API_KEY),lobster_local_test_key)

# =========================
# Setup
# =========================

.PHONY: setup
setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

# =========================
# Local Dev
# =========================

.PHONY: dev
dev:
	@echo "[make] Starting Lobster (dev mode)..."
	$(UVICORN) $(APP_MODULE) --host 127.0.0.1 --port $(PORT) --reload

.PHONY: dev-clean
dev-clean:
	rm -rf $(VENV)

# =========================
# Docker
# =========================

.PHONY: docker-build
docker-build:
	@echo "[make] Building Docker image..."
	docker build -t $(DOCKER_IMAGE) .

.PHONY: docker-run
docker-run:
	@echo "[make] Running Docker container..."
	docker rm -f $(DOCKER_CONTAINER) 2>/dev/null || true
	docker run -d \
		--name $(DOCKER_CONTAINER) \
		-p $(PORT):4000 \
		--env-file $(ENV_FILE) \
		-v "$(DATA_DIR):/app/data" \
		$(DOCKER_IMAGE)

.PHONY: docker-stop
docker-stop:
	@echo "[make] Stopping container..."
	docker rm -f $(DOCKER_CONTAINER) 2>/dev/null || true

.PHONY: docker-logs
docker-logs:
	docker logs -f $(DOCKER_CONTAINER)

# =========================
# Testing
# =========================

.PHONY: test-models
test-models:
	@echo "[make] Testing /v1/models..."
	curl -s $(BASE_URL)/v1/models \
		-H "Authorization: Bearer $(API_KEY)" | jq

.PHONY: test-chat
test-chat:
	@echo "[make] Testing chat..."
	curl -s $(BASE_URL)/v1/chat/completions \
		-H "Authorization: Bearer $(API_KEY)" \
		-H "Content-Type: application/json" \
		-d '{"model":"openclaw","user":"local-test-user","messages":[{"role":"user","content":"Respond with HEALTHY"}]}' | jq

.PHONY: test-stream
test-stream:
	@echo "[make] Testing streaming..."
	curl -N $(BASE_URL)/v1/chat/completions \
		-H "Authorization: Bearer $(API_KEY)" \
		-H "Content-Type: application/json" \
		-d '{"model":"openclaw","user":"local-test-user","stream":true,"messages":[{"role":"user","content":"Respond with HEALTHY"}]}'

# =========================
# Health / Debug
# =========================

.PHONY: health
health:
	curl -s $(BASE_URL)/healthz | jq

.PHONY: debug-env
debug-env:
	@echo "LOBSTER_API_KEY=$(LOBSTER_API_KEY)"
	@echo "API_KEY=$(API_KEY)"

# =========================
# Memory DB
# =========================

.PHONY: db-reset
db-reset:
	@echo "[make] Resetting memory DB..."
	rm -f $(DATA_DIR)/lobster_memory.sqlite3

.PHONY: db-inspect
db-inspect:
	sqlite3 $(DATA_DIR)/lobster_memory.sqlite3 ".tables"
	sqlite3 $(DATA_DIR)/lobster_memory.sqlite3 "SELECT * FROM memories LIMIT 10;"

# =========================
# Reset
# =========================

.PHONY: reset
reset: docker-stop db-reset dev-clean
	@echo "[make] Full reset complete."

