# ConsulApp - UX/UI Review Findings

**Fecha:** 2026-03-05
**Herramienta:** Chrome DevTools + Lighthouse
**Dispositivo:** Mobile (375x812, iPhone X)

## Resumen de Puntuaciones Lighthouse

| Pagina | Accesibilidad | Best Practices | SEO |
|--------|---------------|----------------|-----|
| Login | 96 | 100 | 75 |
| Agenda | 82 | 92 | 90 |
| Pacientes | 95 | 100 | 75 |
| Nuevo Turno | 96 | 100 | 75 |

---

## Issues por Severidad

### Criticos (WCAG 2.1 Level A)

#### 1. Form elements sin labels asociados
**Ubicacion:** Agenda (desktop view)
- `input#agenda-fecha-input` no tiene label
- `select[name=profesional_id]` no tiene label

**Solucion:**
```html
<!-- Antes -->
<input id="agenda-fecha-input" type="date" name="fecha">
<select name="profesional_id" class="input">

<!-- Despues -->
<label for="agenda-fecha-input" class="sr-only">Fecha</label>
<input id="agenda-fecha-input" type="date" name="fecha">

<label for="profesional-select" class="sr-only">Profesional</label>
<select id="profesional-select" name="profesional_id" class="input">
```

#### 2. Contraste de color insuficiente
**Ubicacion:** Pills activos (consultorios)
- Color: #ffffff sobre #ea580c
- Contraste actual: 3.55:1
- Contraste requerido: 4.5:1 (texto normal)

**Solucion:** Oscurecer el color de fondo o usar texto oscuro
```css
/* Opcion A: Fondo mas oscuro */
.pill.is-active {
  background: #c2410c; /* brand-hover */
  color: #fff;
}

/* Opcion B: Agregar font-weight para texto grande */
.pill.is-active {
  font-weight: 700;
  font-size: 14px; /* >= 14px bold solo necesita 3:1 */
}
```

---

### Importantes (WCAG 2.1 Level AA)

#### 3. Meta description faltante
**Ubicacion:** Todas las paginas

**Solucion:** Agregar en `base.html`:
```html
<meta name="description" content="ConsulApp - Sistema de gestion de turnos para profesionales de la salud">
```

#### 4. Error en consola por CSP
**Descripcion:** HTMX intenta aplicar estilos inline que son bloqueados por CSP
**Mensaje:** `Applying inline style violates the following Content Security Policy directive 'style-src 'self'...`

**Solucion:** Agregar hash del estilo o nonce al CSP:
```python
# En la directiva style-src agregar:
style-src 'self' 'sha256-pgn1TCGZX6O77zDvy0oTODMOxemn0oj0LeCnQTRj7Kg=' https://fonts.googleapis.com
```

---

### Menores (Mejoras)

#### 5. Touch targets en grilla
**Ubicacion:** Agenda grid (celdas "+")
- Links "+" tienen min-height 44px (OK)
- Pero en desktop, el area clickeable es muy pequena

**Recomendacion:** Mantener padding minimo en todas las resoluciones

#### 6. Bottom nav no tapa contenido
**Estado:** OK - `padding-bottom: 5.5rem` en `.page-wrap` evita overlap

#### 7. Checkbox "Mis turnos" sin label visible
**Ubicacion:** Agenda filters
**Estado:** Tiene label, pero esta despues del checkbox (orden correcto para a11y)

---

## Checklist de Accesibilidad

| Criterio | Login | Agenda | Pacientes | Nuevo Turno | Admin |
|----------|-------|--------|-----------|-------------|-------|
| Labels en formularios | OK | FAIL | OK | OK | OK |
| Touch targets >= 44px | OK | OK | OK | OK | OK |
| Contraste colores | OK | FAIL | OK | OK | OK |
| No overflow horizontal | OK | OK | OK | OK | OK |
| Estados de error visibles | OK | OK | OK | OK | N/A |
| Bottom nav no tapa | OK | OK | OK | OK | OK |

---

## Acciones Requeridas (Feature 005)

1. **Agregar labels sr-only** a inputs de agenda
2. **Mejorar contraste** de pills activos
3. **Agregar meta description** en base.html
4. **Actualizar CSP** para permitir estilos HTMX
5. **Verificar** fixes con nueva auditoria Lighthouse

---

## Notas Adicionales

- La estructura de accesibilidad (a11y tree) es correcta
- Los roles ARIA estan bien implementados
- La navegacion por teclado funciona correctamente
- El bottom nav tiene `safe-area-inset-bottom` para notch de iPhone
