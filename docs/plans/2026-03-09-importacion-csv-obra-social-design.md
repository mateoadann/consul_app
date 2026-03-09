# Importacion CSV + Obra Social + Campos Paciente

## Nueva entidad ObraSocial

| Campo  | Tipo        | Restriccion       |
|--------|-------------|-------------------|
| id     | Integer     | PK                |
| nombre | String(100) | unique, not null  |

CRUD completo en blueprint `obra_sociales`, acceso solo admin.

## Cambios en Paciente

| Antes                        | Despues                                          |
|------------------------------|--------------------------------------------------|
| `email` (String)             | se elimina                                       |
| `obra_social` (String libre) | `obra_social_id` (FK -> obra_sociales.id, nullable) |
| —                            | `numero_afiliado` (Integer, nullable)            |
| —                            | `apodo` (String(100), nullable)                  |

## Importacion CSV

- Ruta: `POST /pacientes/importar` (solo admin)
- Formato CSV:

```
nombre,apellido,dni,telefono,numero_afiliado,obra_social_id,notas,apodo
Juan,Perez,12345678,1155551234,98765,1,alguna nota,Juancho
```

- Campos obligatorios: `nombre`, `apellido`, `dni`
- Validaciones: DNI unico (skip duplicados), `obra_social_id` debe existir si se proporciona
- Resultado: resumen con creados/saltados/errores
- Pagina con form de upload + tabla de resultados

## Migracion

Una migracion Alembic que:
- Elimine columna `email`
- Elimine columna `obra_social` (string)
- Agregue `obra_social_id` FK -> obra_sociales.id (nullable)
- Agregue `numero_afiliado` Integer (nullable)
- Agregue `apodo` String(100) (nullable)

## Archivos afectados

- `app/models/paciente.py` — campos nuevos
- `app/models/obra_social.py` — nuevo modelo
- `app/models/__init__.py` — registrar ObraSocial
- `app/blueprints/pacientes/` — forms, routes, templates
- `app/blueprints/obra_sociales/` — nuevo blueprint CRUD (admin)
- Templates de pacientes (detalle, nuevo/editar, lista)
- `seed.py` — adaptar a nuevos campos
