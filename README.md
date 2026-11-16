# Proyecto Web E‑Comers Carros

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Aplicación web Fullstack desarrollada en **Python (Flask)** con integración de **Bootstrap** para la interfaz. Incluye autenticación de usuarios, calculadora de consumo energético, integración con API de **Open Charge Map** y base de datos en la nube (**Azure SQL**). Objetivo: Plataforma de comercio electrónico enfocada en carros eléctricos, con funcionalidades de compra, gestión de usuarios y análisis de consumo.

## Tabla de contenidos
- [Instalación paso a paso](#instalación-paso-a-paso)
- [Uso básico](#uso-básico)
- [Ejemplos de API](#ejemplos-de-api)
- [Arquitectura](#arquitectura)
- [Despliegue](#despliegue)
- [Contribución](#contribución)
- [Licencia](#licencia)
- [Checklist antes de entregar](#checklist-antes-de-entregar)

## Instalación paso a paso

1. **Clonar repositorio**
   ```bash
   git clone https://github.com/arsleck/proyecto_web_ecomersCarros.git
   cd proyecto_web_ecomersCarros
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   # En Windows
   venv\Scripts\activate
   # En Linux/macOS
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   Copie el archivo `.env.example` a `.env` y complete los valores:
   ```bash
   cp .env.example .env
   ```
   Luego edite `.env` con su configuración:
   ```env
   # Azure SQL
   DB_SERVER=su_servidor.database.windows.net
   DB_NAME=su_base_de_datos
   DB_USER=su_usuario
   DB_PASS=su_contraseña
   # Seguridad
   SECRET_KEY=una_clave_secreta_muy_segura
   DEBUG=True
   # Open Charge Map
   API_OCM_KEY=su_api_key_de_openchargemap
   ```

5. **Ejecutar la aplicación**
   ```bash
   python run.py
   ```
   El servidor se iniciará en `http://127.0.0.1:5000`.

## Uso básico

- **URL principal**: `http://127.0.0.1:5000/`
- **Rutas clave**:
  - `/` - Página de inicio
  - `/usuarios/login` - Inicio de sesión
  - `/usuarios/register` - Registro de nuevos usuarios
  - `/vehiculos` - Listado de vehículos eléctricos disponibles
  - `/calculadora` - Herramienta para calcular consumo energético
  - `/mapa` - Mapa de estaciones de carga (Open Charge Map)
  - `/cuenta` - Perfil de usuario
  - `/noticias` - Sección de noticias sobre movilidad eléctrica

### Flujo de ejemplo

1. **Registro de usuario**
   - Diríjase a `/usuarios/register`
   - Complete el formulario con nombre, email, teléfono y contraseña
   - Confirme el registro y será redirigido al login

2. **Compra de vehículo**
   - Inicie sesión
   - Visite `/vehiculos` para ver el catálogo
   - Seleccione un vehículo y haga clic en "Comprar"
   - Siga el proceso de pago (simulado)

3. **Cálculo de consumo**
   - Acceda a `/calculadora`
   - Ingrese los kilómetros recorridos y el tipo de vehículo
   - Obtendrá el consumo estimado en kWh y el costo aproximado

## Ejemplos de API

Aunque la aplicación es principalmente renderizada del servidor, algunos endpoints devuelven JSON útiles para integración.

### Obtener estaciones de carga (Open Charge Map)
```bash
curl -X GET "http://127.0.0.1:5000/mapa/" \
  -H "Cookie: session=tu_session_cookie"
```
**Respuesta JSON (simplificada):**
```json
{
  "estaciones": [
    {
      "AddressInfo": {
        "Title": "Estación de carga rápida",
        "AddressLine1": "Carrera 123 #45-67",
        "Town": "Bogotá",
        "StateOrProvince": "Cundinamarca",
        "Postcode": "110111",
        "CountryID": "CO",
        "Latitude": 4.7110,
        "Longitude": -74.0721
      },
      "Connections": [
        {
          "ConnectionTypeID": 25,
          "CurrentTypeID": 30,
          "Quantity": 4,
          "PowerKW": 150
        }
      ]
    }
  ],
  "titulo_pagina": "Mapa de Estaciones🗺️"
}
```

### Obtener lista de vehículos (JSON alternativo)
```bash
curl -X GET "http://127.0.0.1:5000/vehiculos/data"
```
*Nota: Este endpoint puede no existir en la versión actual; se muestra como ejemplo de posible extensión.*

## Arquitectura

```
proyecto_web_ecomersCarros/
├── app/                     # Paquete principal de la aplicación
│   ├── __init__.py          # Factory de la aplicación Flask y configuración
│   ├── models/              # Modelos SQLAlchemy (Usuario, Noticia, etc.)
│   │   ├── usuario.py
│   │   └── noticia.py
│   ├── routes/              # Blueprints organizados por funcionalidad
│   │   ├── main_routes.py
│   │   ├── usuarios_routes.py
│   │   ├── vehiculos_routes.py
│   │   ├── noticias_routes.py
│   │   ├── calculadora_routes.py
│   │   ├── cuenta_routes.py
│   │   └── mapa_routes.py   # Integración con Open Charge Map
│   ├── static/              # Archivos estáticos (CSS, JS, imágenes)
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/           # Plantillas HTML con Jinja2
│       ├── main/
│       ├── usuarios/
│       ├── vehiculos/
│       ├── noticias/
│       ├── calculadora/
│       ├── mapa/
│       └── partials/
├── migrations/              # Esquemas de base de datos generados por Flask-Migrate
├── requirements.txt         # Dependencias de Python
├── run.py                   # Punto de entrada de la aplicación
├── Dockerfile               # Configuración para contenedores (Despliegue en Railway/Azure)
├── Procfile                 # Declaración de procesos para plataformas como Heroku/Railway
└── .env.example             # Plantilla de variables de entorno
```

### Descripción de componentes clave

- **`app/__init__.py`**: Crea la instancia de Flask, configura la conexión a Azure SQL, inicializa extensiones (SQLAlchemy, Migrate) y registra los blueprints.
- **Modelos**: Definen la estructura de la base de datos usando SQLAlchemy ORM.
- **Rutas (Blueprints)**: Cada archivo en `routes/` maneja un grupo de URLs relacionadas (autenticación, vehículos, etc.).
- **Plantillas**: Utilizan Bootstrap 5 para una interfaz responsive y consistente.
- **Estáticos**: Contienen estilos personalizados y lógica del cliente (JavaScript).

## Despliegue

### En Railway

1. Cree una cuenta en [Railway.app](https://railway.app/)
2. Nuevo proyecto → Deploy from GitHub → Seleccione este repositorio
3. Railway detectará automáticamente el `Dockerfile` y el `Procfile`
4. Configure las variables de entorno en la pestaña *Variables*:
   - `DB_SERVER`, `DB_NAME`, `DB_USER`, `DB_PASS`
   - `SECRET_KEY`
   - `API_OCM_KEY`
   - `PORT` (Railway lo proporciona automáticamente, pero está definido en Dockerfile)
5. Habilite la opción de *Deployments* automáticos si lo desea.

### En Azure App Service

1. Cree un recurso *App Service* en el portal de Azure
2. Configure el stack de publicación en *Docker Container*
3. Imagen: Use el Dockerfile del repositorio (puede construirlo y subirlo a Azure Container Registry o usar despliegue directo desde GitHub Actions)
4. En *Configuración > Aplicaciones*, agregue las variables de entorno igual que en el archivo `.env`
5. Asegúrese de que el puerto interno coincida con el esperado por Gunicorn (8080 según Dockerfile)
6. Habilite el despliegue continuo desde GitHub si lo prefiere.

### Despliegue local con Docker

```bash
# Construir la imagen
docker build -t ecomers-carros .

# Ejecutar el contenedor
docker run -p 8080:8080 --env-file .env ecomers-carros
```

## Contribución

1. **Hacer fork** del repositorio
2. **Crear una rama** para su feature o fix:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Realizar sus cambios** y commitear con mensajes descriptivos
4. **Push** a su fork:
   ```bash
   git push origin feature/nueva-funcionalidad
   ```
5. **Abrir un Pull Request** contra la rama `main` del repositorio original
6. Espere revisión y aprobado por los mantenedores

### Guía de estilo de commits

- `feat:` para nuevas características
- `fix:` para correcciones de errores
- `docs:` para cambios en documentación
- `style:` para formato, indentación, etc.
- `refactor:` para refactorización de código
- `test:` para añadir o modificar pruebas
- `chore:` para tareas de mantenimiento

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.

## Checklist antes de entregar

- [ ] Revisar dependencias en `requirements.txt` (versiones actualizadas y compatibles)
- [ ] Verificar que todas las variables de entorno necesarias estén definidas en `.env`
- [ ] Asegurarse de que las migraciones de la base de datos estén aplicadas (`flask db upgrade` o mediante `db.create_all()` en `run.py`)
- [ ] Confirmar que los seeds de datos iniciales (si los hay) se hayan ejecutado
- [ ] Probar localmente las funcionalidades clave: registro, login, cálculo, mapa
- [ ] Verificar que no haya datos sensibles commiteados (eliminar cualquier `.env` real)
- [ ] Asegurarse de que el `README.md` esté actualizado y sea claro para nuevos contribuyentes

---

*README generado automáticamente el 2026-06-05*
## Planeta Verde – ejecución rápida (módulo de catálogo y ventas)
```bash
pip install -r requirements.txt -r requirements-dev.txt
# .env: DB_SERVER/DB_NAME/DB_USER/DB_PASS (Azure) o DATABASE_URL=sqlite:///local.db, SECRET_KEY
python run.py          # crea tablas, admin (admin/Admin1234) y 10 vehículos
# Catálogo: http://localhost:5000/catalogo/
pytest --cov=app       # 70 pruebas, cobertura 100 %
pytest -m rendimiento -s   # RNF-03, RNF-04 y RNF-09 (p95, carga con 100 vehículos y 300 usuarios)
python scripts/preparar_demo.py   # datos de demostración para grabar el video (ver abajo)
```
Variables de entorno de Planeta Verde (ver `.env.example`): `SECRET_KEY`, `FORCE_HTTPS=1` (cookie Secure detrás de HTTPS),
`ADMIN_PASSWORD` (contraseña del admin sembrado) y `MAIL_SERVER` / `MAIL_USER` / `MAIL_PASS` (envío SMTP del enlace de
recuperación; sin ellas se usa el modo desarrollo, que muestra el enlace en pantalla y **no debe usarse en producción**).

Documentos: informe de calidad `docs/Informe_Planeta_Verde_APA.docx` · diagramas `docs/diagramas.md` ·
migración para Azure SQL `docs/migracion.sql` (elimina la columna `password`; los usuarios antiguos deben restablecer su clave) ·
lista de chequeo responsive/multinavegador `docs/checklist_responsive.md` ·
medición contra un despliegue real: `python scripts/medir_rendimiento.py https://mi-app.azurewebsites.net`.
