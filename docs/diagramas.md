# Diagramas (Mermaid – se renderizan en GitHub)

## Despliegue
```mermaid
flowchart LR
  A[Cliente Web<br/>HTML/CSS/JS + Bootstrap] -- HTTP/HTTPS --> B[Servidor Flask<br/>Gunicorn · Blueprints]
  B -- pyodbc / SQLAlchemy --> C[(Azure SQL)]
  B -- REST --> D[Open Charge Map API]
```

## Entidad–relación (implementado)
```mermaid
erDiagram
  USUARIOS { int id PK  string nombre UK  string email UK  string password_hash  string telefono  string rol }
  NOTICIAS { int id PK  string titulo  text contenido  string imagen }
```
*Pendiente (extensión): VEHICULOS, VENTAS, TOKENS_RECUPERACION.*

## Casos de uso
```mermaid
flowchart LR
  U((Usuario)) --> R[Registrarse] & L[Iniciar/cerrar sesión] & V[Ver catálogo y fichas] & K[Calculadora de consumo] & M[Mapa de cargadores] & N[Leer noticias] & Cu[Editar/eliminar cuenta]
  Ad((Administrador)) --> CN[CRUD noticias]
```

## Secuencia – login
```mermaid
sequenceDiagram
  Cliente->>Flask: POST /login (usuario, password)
  Flask->>AzureSQL: SELECT usuario por nombre
  AzureSQL-->>Flask: fila + password_hash
  Flask->>Flask: check_password_hash()
  Flask-->>Cliente: 302 /noticias/inicio (session)
```
