SHELL := /bin/bash
.DEFAULT_GOAL := help

COMPOSE ?= docker compose
COMPOSE_PROD ?= docker compose -f docker-compose.prod.yml
APP_SERVICE ?= app
PROD_APP_SERVICE ?= app
PYTHON ?= python3
VENV ?= .venv
FLASK_APP ?= wsgi.py
FLASK_ENV ?= development
NPM_NETWORK ?= npm_proxy

VENV_PY := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip
VENV_FLASK := $(VENV)/bin/flask
VENV_PYTEST := $(VENV)/bin/pytest
PYTEST_FLAGS ?= -vv -rA

.PHONY: help env venv install run seed-local test test-postgres clean-pyc \
	up up-build down restart logs ps shell db-init db-upgrade db-migrate db-bootstrap \
	seed docker-test docker-test-db docker-db-upgrade prod-up prod-down prod-restart \
	prod-logs prod-ps prod-shell prod-db-upgrade deploy backup-auto backup-manual \
	vapid-keys notify-birthdays

help: ## Muestra esta ayuda
	@awk 'BEGIN {FS = ":.*##"; printf "\nUso:\n  make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_.-]+:.*?##/ {printf "  %-14s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

env: ## Crea .env desde .env.example si falta
	@if [ ! -f .env ]; then cp .env.example .env; echo "[ok] .env creado"; else echo "[ok] .env ya existe"; fi

venv: ## Crea el virtualenv local
	@if [ ! -d $(VENV) ]; then $(PYTHON) -m venv $(VENV); fi

install: venv ## Instala dependencias Python en local
	$(VENV_PIP) install -r requirements.txt

run: install ## Levanta la app local en debug
	FLASK_APP=$(FLASK_APP) FLASK_ENV=$(FLASK_ENV) $(VENV_FLASK) run --debug

seed-local: install ## Ejecuta seed.py en local
	$(VENV_PY) seed.py

test: install ## Ejecuta tests en local (verbose)
	$(VENV_PYTEST) $(PYTEST_FLAGS)

test-postgres: install ## Ejecuta tests marcados postgres (definir TEST_DATABASE_URL)
	@if [ -z "$(TEST_DATABASE_URL)" ]; then echo "Defini TEST_DATABASE_URL para este target"; exit 1; fi
	TEST_DATABASE_URL=$(TEST_DATABASE_URL) $(VENV_PYTEST) $(PYTEST_FLAGS) -m postgres

clean-pyc: ## Limpia archivos temporales de Python
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) for p in pathlib.Path('.').rglob('__pycache__')]"

up: env ## Levanta stack docker y deja esquema listo via migraciones
	$(MAKE) up-build
	$(MAKE) docker-db-upgrade

up-build: env ## Build + up docker en dev (sin migrar)
	$(COMPOSE) up -d --build

down: ## Baja stack docker (dev)
	$(COMPOSE) down --remove-orphans

restart: ## Reinicia stack docker (dev)
	$(COMPOSE) down
	$(MAKE) up

logs: ## Sigue logs del stack dev
	$(COMPOSE) logs -f --tail=100

ps: ## Lista servicios del stack dev
	$(COMPOSE) ps

shell: ## Abre shell dentro del contenedor app (dev)
	$(COMPOSE) exec $(APP_SERVICE) sh

db-init: ## Inicializa migraciones (solo primera vez)
	@if [ -f migrations/env.py ]; then \
		echo "[ok] migrations ya inicializadas"; \
	else \
		$(COMPOSE) exec $(APP_SERVICE) flask --app wsgi.py db init; \
	fi

db-upgrade: ## Aplica migraciones en docker
	@if [ ! -f migrations/env.py ]; then echo "Faltan archivos de migracion. Ejecuta: make db-init"; exit 1; fi
	$(COMPOSE) up -d db $(APP_SERVICE)
	$(COMPOSE) exec db sh -lc 'until pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" >/dev/null 2>&1; do sleep 1; done'
	$(COMPOSE) exec $(APP_SERVICE) flask --app wsgi.py db upgrade

db-migrate: ## Crea migracion (usar: make db-migrate msg="texto")
	@if [ -z "$(msg)" ]; then echo "Uso: make db-migrate msg=\"descripcion\""; exit 1; fi
	@if [ ! -f migrations/env.py ]; then echo "Faltan archivos de migracion. Ejecuta: make db-init"; exit 1; fi
	$(COMPOSE) exec $(APP_SERVICE) flask --app wsgi.py db migrate -m "$(msg)"

db-bootstrap: env ## Inicializa extensiones y aplica migraciones (dev)
	$(COMPOSE) up -d db $(APP_SERVICE)
	$(COMPOSE) exec db sh -lc 'until pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" >/dev/null 2>&1; do sleep 1; done'
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"'
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"'
	@alembic_table=$$($(COMPOSE) exec -T db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -tAc "SELECT to_regclass('\''alembic_version'\'')"' | tr -d '[:space:]'); \
	if [ "$$alembic_table" = "alembic_version" ]; then \
		$(MAKE) db-upgrade; \
	else \
		echo "[info] Base nueva detectada: bootstrap de schema + stamp head"; \
		$(COMPOSE) exec $(APP_SERVICE) python -c 'from app import create_app; from app.extensions import db; import app.models; app=create_app(); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop()'; \
		$(COMPOSE) exec $(APP_SERVICE) flask --app wsgi.py db stamp head; \
	fi
	$(COMPOSE) exec $(APP_SERVICE) flask --app wsgi.py ensure-admin

docker-db-upgrade: db-bootstrap ## Alias: migraciones en Docker dev

seed: ## Ejecuta seed.py en docker
	$(COMPOSE) exec $(APP_SERVICE) python seed.py

docker-test-db: env ## Recrea DB de tests aislada en Docker
	$(COMPOSE) up -d db
	$(COMPOSE) exec db sh -lc 'until pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" >/dev/null 2>&1; do sleep 1; done'
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "DROP DATABASE IF EXISTS $$POSTGRES_TEST_DB;"'
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d postgres -v ON_ERROR_STOP=1 -c "CREATE DATABASE $$POSTGRES_TEST_DB;"'
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_TEST_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"'
	$(COMPOSE) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_TEST_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"'

docker-test: docker-test-db ## Ejecuta tests dentro de Docker con DB aislada (verbose)
	$(COMPOSE) run --rm $(APP_SERVICE) sh -lc 'if [ -z "$$TEST_DATABASE_URL" ]; then echo "TEST_DATABASE_URL no esta definido"; exit 1; fi; pytest $(PYTEST_FLAGS)'

test-coverage: install ## Ejecuta tests con reporte de cobertura
	$(VENV_PYTEST) --cov=app --cov-report=html --cov-report=term $(PYTEST_FLAGS)

prod-up: env ## Levanta stack de produccion (build + detached)
	@docker network inspect $(NPM_NETWORK) >/dev/null 2>&1 || docker network create $(NPM_NETWORK)
	$(COMPOSE_PROD) up -d --build

prod-down: ## Baja stack de produccion
	$(COMPOSE_PROD) down --remove-orphans

prod-restart: ## Reinicia stack de produccion
	$(COMPOSE_PROD) down
	$(MAKE) prod-up

prod-logs: ## Sigue logs del stack de produccion
	$(COMPOSE_PROD) logs -f --tail=100

prod-ps: ## Lista servicios del stack de produccion
	$(COMPOSE_PROD) ps

prod-shell: ## Abre shell dentro del contenedor app (produccion)
	$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) sh

prod-db-upgrade: env ## Aplica migraciones en stack de produccion
	@if [ ! -f migrations/env.py ]; then echo "Faltan archivos de migracion. Ejecuta: make db-init"; exit 1; fi
	$(COMPOSE_PROD) up -d db redis $(PROD_APP_SERVICE)
	$(COMPOSE_PROD) exec db sh -lc 'until pg_isready -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" >/dev/null 2>&1; do sleep 1; done'
	$(COMPOSE_PROD) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS btree_gist;"'
	$(COMPOSE_PROD) exec db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"'
	@alembic_table=$$($(COMPOSE_PROD) exec -T db sh -lc 'psql -U "$$POSTGRES_USER" -d "$$POSTGRES_DB" -tAc "SELECT to_regclass('\''alembic_version'\'')"' | tr -d '[:space:]'); \
	if [ "$$alembic_table" = "alembic_version" ]; then \
		$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) flask --app wsgi.py db upgrade; \
	else \
		echo "[info] Base nueva detectada: bootstrap de schema + stamp head"; \
		$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) python -c 'from app import create_app; from app.extensions import db; import app.models; app=create_app("production"); ctx=app.app_context(); ctx.push(); db.create_all(); ctx.pop()'; \
		$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) flask --app wsgi.py db stamp head; \
	fi
	$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) flask --app wsgi.py ensure-admin

# ── Push Notifications ────────────────────────────
notify-birthdays: ## Envia notificaciones push de cumpleanos (cron: 0 8 * * *)
	$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) flask --app wsgi.py notify birthdays

vapid-keys: ## Genera par de claves VAPID para push notifications
	@$(COMPOSE_PROD) exec $(PROD_APP_SERVICE) python3 -c "\
	import base64; \
	from py_vapid import Vapid; \
	from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat; \
	v = Vapid(); v.generate_keys(); \
	pub = base64.urlsafe_b64encode(v.public_key.public_bytes(Encoding.X962, PublicFormat.UncompressedPoint)).rstrip(b'=').decode(); \
	print('Agrega estas claves a tu .env:\n'); \
	print('VAPID_PRIVATE_KEY=' + v.private_pem().decode().strip()); \
	print('VAPID_PUBLIC_KEY=' + pub)"

# ── Deploy & Backups ──────────────────────────────
deploy: ## Ejecuta deploy completo en el VPS
	bash scripts/deploy.sh

backup-auto: ## Ejecuta backup automatico de la DB (produccion)
	bash scripts/backup-db.sh auto

backup-manual: ## Ejecuta backup manual/pre-deploy de la DB (produccion)
	bash scripts/backup-db.sh manual
