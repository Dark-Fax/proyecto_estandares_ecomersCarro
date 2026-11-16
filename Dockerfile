# Usamos una versión ligera de Python basada en Debian 11 (Bullseye)
# Esto es importante para compatibilidad con los drivers de Microsoft
FROM python:3.11-slim-bullseye

# Establecemos la carpeta de trabajo
WORKDIR /app

# 1. INSTALACIÓN DE DRIVERS DEL SISTEMA (La parte que fallaba antes)
# Instalamos curl, gnupg y las librerías ODBC básicas
RUN apt-get update && apt-get install -y curl gnupg2 unixodbc unixodbc-dev build-essential libpq-dev \
    # Descargamos la llave de Microsoft
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    # Agregamos el repositorio de Microsoft para Debian 11
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    # Actualizamos e instalamos el Driver 17 aceptando la licencia
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    # Limpiamos archivos temporales para ahorrar espacio
    && apt-get clean

# 2. INSTALACIÓN DE LIBRERÍAS PYTHON
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. COPIAR TU PROYECTO
COPY . .

# 4. CONFIGURACIÓN DE ARRANQUE
# Railway usa la variable PORT, así que configuramos Gunicorn para usarla
ENV PORT=8080
CMD gunicorn "app:create_app()" --bind 0.0.0.0:$PORT