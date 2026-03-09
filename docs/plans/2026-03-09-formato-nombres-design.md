# Formato de Nombres en Agenda - Design

## Goal

Permitir al admin configurar cómo se muestran los nombres de pacientes y profesionales en los chips de la agenda, con previsualización en vivo. Configuración global e independiente para cada entidad.

## Opciones de formato

| Key | Ejemplo (nombre=Pedro, apellido=Gomez, apodo=Pedrito) |
|-----|-------------------------------------------------------|
| `nombre` | Pedro |
| `nombre_apellido` | Pedro Gomez |
| `nombre_inicial` | Pedro G. |
| `apodo` | Pedrito (fallback: Pedro G.) |
| `apodo_inicial` | Pedrito G. (fallback: Pedro G.) |

Fallback siempre a `nombre_inicial` cuando no hay apodo.

Default: `nombre_inicial` para ambos.

## Modelo de datos

### AppConfig (nuevo)

Tabla key-value para configuración global:

- `formato_nombre_paciente` → uno de los keys de arriba
- `formato_nombre_profesional` → uno de los keys de arriba

### Profesional: agregar campo `apodo`

String(100), nullable. Migración + actualizar form.

## Lógica

Helper `format_display_name(entity, format_key)` expuesto como filtro Jinja `display_name`. Config cacheada en `g` por request.

## UI Admin

Sección "Formato de nombres" en `/admin/formato-nombres`:
- Dos selects independientes (paciente, profesional)
- Preview en vivo con JS puro (datos ejemplo hardcodeados)
- Botón guardar

## Templates afectados

- `agenda/_grilla.html`
- `agenda/_slot.html`
- `agenda/_timeline.html`
- `agenda/_ocupados.html`
