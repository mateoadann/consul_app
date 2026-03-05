# ConsulApp

Sistema mobile-first para gestion de turnos de centro medico con Flask + HTMX + PostgreSQL.

## Estado general

- App server-rendered (Flask + Jinja + HTMX), sin SPA ni API separada.
- App factory en `app/__init__.py`.
- Entry point WSGI en `wsgi.py`.
- Configuracion por variables de entorno en `config.py` y `.env`.
- Doble modo de despliegue:
  - desarrollo con `docker-compose.yml`
  - produccion con `docker-compose.prod.yml` (`web`, `app`, `db`, `redis`)

## Stack

- Flask (SSR + fragmentos HTMX)
- SQLAlchemy + Flask-Migrate
- Flask-Login + Flask-Session
- PostgreSQL (tsrange + exclusion constraints)
- Docker Compose + Gunicorn

## Requisitos

- Docker y Docker Compose, o Python 3.12 + Postgres 16
- Extensiones Postgres `btree_gist` y `pg_trgm` (incluidas en `init-db.sql`)

## Arranque rapido

### Docker dev (recomendado)

```bash
make env
make up-build
make docker-db-upgrade
# opcional
make seed
```

Abrir: `http://localhost:5002`

Usuario inicial demo:

- admin / admin123

Tambien puedes usar:

```bash
make up
```

`make up` equivale a `up-build` + `docker-db-upgrade`.

### Local sin Docker

```bash
make venv
make install
make env
make run
# opcional
make seed-local
```

## Produccion

Stack de produccion con Nginx reverse proxy + app + db:

```bash
make env
make prod-up
make prod-db-upgrade
```

`make prod-up` crea automaticamente la red externa `${NPM_NETWORK}` (default `npm_proxy`) para integracion con Nginx Proxy Manager.

Puertos por defecto:

- app web: `http://localhost:8080` (entra al flujo normal de login)

Operaciones utiles:

```bash
make prod-logs
make prod-ps
make prod-down
```

## Atajos con Make

```bash
make help                # lista todos los targets
make up                  # dev: up + migraciones
make down                # dev: baja stack
make logs                # dev: logs
make db-migrate msg="x"  # crea migracion
make db-upgrade          # aplica migraciones (dev)
make docker-test         # tests docker con DB aislada
```

## Estructura

- `app/models`: dominio principal (users, pacientes, profesionales, consultorios, turnos, auditoria)
- `app/blueprints`: auth, agenda, turnos, pacientes, profesionales, consultorios, admin
- `app/services/disponibilidad.py`: consulta de agenda, conflictos y sugerencias
- `app/templates`: paginas SSR y fragmentos HTMX

## Estado de turnos

- reservado -> confirmado -> atendido
- reservado/confirmado -> cancelado
- atendido y cancelado son terminales

## Repeticion de turnos (MVP)

- En `Nuevo turno`, activa **Repetir turno** para crear una serie.
- Puedes agregar multiples patrones por semana (dia + hora inicio/fin + consultorio).
- Define cada cuantas semanas se repite y una fecha limite.
- La serie se procesa en modo parcial: crea lo disponible y registra lo fallido.

## Tests

Los tests de integracion requieren Postgres real:

```bash
make docker-test
```

`make docker-test` recrea una base aislada (`consul_app_test`) antes de correr, para no tocar datos de `consul_app`.
