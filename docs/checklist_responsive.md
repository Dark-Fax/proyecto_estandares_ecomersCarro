# Checklist de pruebas responsive y multinavegador (RNF-05 y RNF-06)

**Proyecto:** Planeta Verde – Concesionario Eco · **Prueba:** P-06 del informe · **Norma:** ISO/IEC 25010 (usabilidad – diseño responsivo; portabilidad – adaptabilidad)

## 1. Preparación

1. Iniciar la aplicación (`python run.py`) o usar la URL desplegada.
2. Tener a mano dos cuentas: `admin / Admin1234` y un cliente registrado (p. ej. `ana / Clave1234`).
3. Datos mínimos: catálogo sembrado (10 vehículos). Para la prueba de capacidad, ejecutar antes `pytest tests/test_rendimiento.py`.
4. Anotar versión de cada navegador y sistema operativo en la tabla de resultados.

### Cómo cambiar el ancho de la ventana

| Navegador | Herramienta | Atajo |
|---|---|---|
| Chrome / Edge | Modo dispositivo | `F12` → icono de dispositivo (`Ctrl+Shift+M`) → *Dimensions: Responsive* → escribir ancho |
| Firefox | Vista de diseño adaptable | `Ctrl+Shift+M` → escribir ancho |
| Safari (macOS) | Modo de diseño adaptable | *Desarrollar* → *Entrar en modo de diseño adaptable* (activar menú Desarrollar en Ajustes → Avanzado) |

Anchos obligatorios: **320 px** (celular pequeño), **768 px** (tablet), **1920 px** (escritorio). Probar también la rotación 320 × 568 → 568 × 320.

## 2. Criterios de aceptación por ancho (aplican a cada pantalla)

- [ ] **Sin scroll horizontal** en toda la página (el contenido nunca excede el ancho).
- [ ] Texto legible sin hacer zoom (≥ 14 px efectivos) y sin solaparse con otros elementos.
- [ ] Botones y enlaces utilizables con el dedo (área táctil ≥ 40 × 40 px aprox.) y sin quedar tapados.
- [ ] Imágenes proporcionadas: no se deforman ni se salen de su tarjeta.
- [ ] Tablas (ventas, inventario, usuarios) se pueden leer: caben o permiten desplazamiento interno.
- [ ] Menú de navegación accesible (sidebar / barra superior): se llega a Catálogo, Cuenta y Cerrar sesión.
- [ ] Mensajes de error y confirmación visibles y completos (RNF-08).

## 3. Pantallas a recorrer

| # | Pantalla | URL | Sesión | Qué verificar además |
|---|---|---|---|---|
| 1 | Login | `/login` | No | Formulario centrado, campos ocupan el ancho útil |
| 2 | Registro | `/register` | No | Los 4 campos visibles; mensaje de validación legible |
| 3 | Catálogo con filtros | `/catalogo/` | No | Filtros se apilan en 320 px; tarjetas de 1 columna (móvil), 3 (escritorio); distintivo **Planeta Verde** visible; paginación utilizable |
| 4 | Detalle de vehículo | `/catalogo/1` | Cliente | Ficha técnica con CO₂; botón **Solicitar compra** visible |
| 5 | Mis compras / comprobante | `/catalogo/ventas` | Cliente | Descarga del PDF funciona |
| 6 | Calculadora | `/calculadora/` | Cliente | Formulario y resultado sin cortarse |
| 7 | Mapa de estaciones | `/mapa/` | Cliente | Mapa ocupa el ancho; controles de zoom táctiles |
| 8 | Noticias | `/noticias/listar` | Cliente | Tarjetas e imágenes proporcionadas |
| 9 | Cuenta | `/cuenta` | Cliente | Formulario de edición y botón eliminar separados |
| 10 | Inventario (admin) | `/catalogo/admin/inventario` | Admin | Tabla con acciones **Registrar venta / Eliminar** accesibles |
| 11 | Usuarios (admin) | `/catalogo/admin/usuarios` | Admin | Tabla legible |
| 12 | Dashboard ambiental | `/catalogo/admin/dashboard` | Admin | Porcentaje Planeta Verde visible |
| 13 | Recuperar / restablecer contraseña | `/catalogo/recuperar` | No | Formulario y mensaje de confirmación |

## 4. Flujo funcional mínimo en cada navegador (RNF-06)

1. Registrarse → iniciar sesión → cerrar sesión.
2. Filtrar el catálogo por motor *eléctrico* y precio máximo; limpiar filtros.
3. Abrir un vehículo y **solicitar compra** (estado pasa a *pendiente*).
4. Como admin: **registrar venta**; descargar el **comprobante PDF** (impacto ambiental visible).
5. Abrir el **dashboard ambiental**.
6. Verificar en la consola del navegador (`F12` → Console) que **no hay errores en rojo**.

## 5. Matriz de resultados (marcar ✔ cumple · ✘ falla · – no aplica)

| Navegador (versión) | SO | 320 px | 768 px | 1920 px | Flujo (sec. 4) | Errores de consola | Evidencia (captura) |
|---|---|:-:|:-:|:-:|:-:|:-:|---|
| Chrome ( ) | | | | | | | |
| Firefox ( ) | | | | | | | |
| Edge ( ) | | | | | | | |
| Safari ( ) | | | | | | | |

## 6. Registro de defectos

| ID | Pantalla | Ancho | Navegador | Descripción | Gravedad (alta/media/baja) | Estado |
|---|---|---|---|---|---|---|
| D-01 | | | | | | |

## 7. Criterio de cierre

- **RNF-05 cumple** si las 13 pantallas cumplen la sección 2 a 320, 768 y 1920 px en al menos un navegador.
- **RNF-06 cumple** si el flujo de la sección 4 se completa sin errores en **los cuatro** navegadores.
- Si Safari no está disponible (requiere macOS/iOS), registrarlo como *no verificado* y justificar; no marcar el RNF-06 como cumplido por completo.
- Guardar las capturas en `docs/evidencias/responsive/` con el formato `navegador_ancho_pantalla.png`.

**Riesgos responsive detectados al revisar el código (verificar primero):**
- `Dashboard.css` (calculadora y panel), `Vehiculo.css` (listado de vehículos) y `mapa.css` **no contienen ningún `@media`**: son los candidatos más probables a fallar a 320 px.
- `Cuenta.css`, `Dashboard.css`, `Vehiculo.css` y `Visual.css` fijan `body { height: 100vh; overflow: hidden }` con un `.sidebar` de 250 px: en pantallas pequeñas el contenido puede quedar cortado y sin posibilidad de desplazarse.
- Las pantallas del catálogo (`/catalogo/...`) usan Bootstrap 5 (rejilla responsive) y, en principio, se adaptan mejor.
