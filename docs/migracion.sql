/* =====================================================================================
   Planeta Verde - Concesionario Eco
   MIGRACION PARA AZURE SQL DATABASE (T-SQL)            Requerimientos: RNF-01, RF-04..RF-15
   -------------------------------------------------------------------------------------
   Qué hace (en orden):
     1. Asegura que usuarios tenga password_hash (Bcrypt) y elimina la columna `password`
        (texto plano) -> cumple RNF-01.
     2. Invalida los hashes que no sean Bcrypt costo 10 (ver ADVERTENCIA).
     3. Crea vehiculos, ventas y tokens_recuperacion con sus llaves, unicidad y chequeos.
   Es IDEMPOTENTE: se puede ejecutar más de una vez sin error ni pérdida de datos.
   Hacer COPIA DE SEGURIDAD antes (Azure Portal > Base de datos > Restaurar / exportar .bacpac).

   ADVERTENCIA - CONTRASEÑAS
   Las contraseñas guardadas con el esquema anterior (texto plano en `password`, o cualquier
   valor que no sea un hash Bcrypt "$2b$10$...") NO se pueden convertir: el sistema nunca
   conoció la contraseña original en forma segura y, por diseño, Bcrypt es irreversible.
   Por eso, tras esta migración, TODOS esos usuarios deben restablecer su contraseña:
     * desde /catalogo/recuperar (enlace temporal de 15 minutos, enviado por correo), o
     * volviendo a registrarse, o
     * el administrador reasigna una contraseña desde el sistema.
   El paso 2 deja password_hash = NULL en esas cuentas; check_password() devuelve False para
   ellas, de modo que no es posible entrar con una contraseña vieja ni con un hash inválido.
   La cuenta `admin` se recrea con la contraseña de la variable ADMIN_PASSWORD al ejecutar
   `python run.py` (seed) si no existe; si ya existe con hash inválido, usar /catalogo/recuperar.
   ===================================================================================== */

SET NOCOUNT ON;
GO

/* =========================== PASO 1: usuarios (RNF-01) =========================== */
IF OBJECT_ID('dbo.usuarios', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.usuarios (
        id            INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_usuarios PRIMARY KEY,
        nombre        VARCHAR(100) NOT NULL CONSTRAINT UQ_usuarios_nombre UNIQUE,
        email         VARCHAR(70)  NOT NULL CONSTRAINT UQ_usuarios_email  UNIQUE,
        password_hash VARCHAR(512) NULL,
        telefono      VARCHAR(10)  NOT NULL,
        rol           VARCHAR(50)  NOT NULL CONSTRAINT DF_usuarios_rol DEFAULT 'usuario'
    );
END;
GO

IF COL_LENGTH('dbo.usuarios', 'password_hash') IS NULL
    ALTER TABLE dbo.usuarios ADD password_hash VARCHAR(512) NULL;
GO

/* Si `password` tiene DEFAULT, CHECK o índices, SQL Server no deja eliminarla: se quitan antes. */
IF COL_LENGTH('dbo.usuarios', 'password') IS NOT NULL
BEGIN
    DECLARE @sql NVARCHAR(MAX) = N'';

    SELECT @sql += N'ALTER TABLE dbo.usuarios DROP CONSTRAINT ' + QUOTENAME(dc.name) + N';'
    FROM sys.default_constraints dc
    JOIN sys.columns c ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
    WHERE dc.parent_object_id = OBJECT_ID('dbo.usuarios') AND c.name = 'password';

    SELECT @sql += N'ALTER TABLE dbo.usuarios DROP CONSTRAINT ' + QUOTENAME(cc.name) + N';'
    FROM sys.check_constraints cc
    JOIN sys.columns c ON c.object_id = cc.parent_object_id AND c.column_id = cc.parent_column_id
    WHERE cc.parent_object_id = OBJECT_ID('dbo.usuarios') AND c.name = 'password';

    SELECT @sql += N'DROP INDEX ' + QUOTENAME(i.name) + N' ON dbo.usuarios;'
    FROM sys.indexes i
    JOIN sys.index_columns ic ON ic.object_id = i.object_id AND ic.index_id = i.index_id
    JOIN sys.columns c ON c.object_id = ic.object_id AND c.column_id = ic.column_id
    WHERE i.object_id = OBJECT_ID('dbo.usuarios') AND c.name = 'password'
      AND i.is_primary_key = 0 AND i.is_unique_constraint = 0;

    EXEC sp_executesql @sql;

    ALTER TABLE usuarios DROP COLUMN password;   -- <- elimina el texto plano (RNF-01)
END;
GO

/* ====================== PASO 2: invalidar hashes que no son Bcrypt ====================== */
/* Válido = Bcrypt con costo de dos dígitos (>= 10): $2a$/$2b$/$2y$ + 10..39 + $.  */
UPDATE dbo.usuarios
   SET password_hash = NULL
 WHERE password_hash IS NOT NULL
   AND password_hash NOT LIKE '$2[aby]$[1-3][0-9]$%';
GO

/* ====================== PASO 3: tablas del catálogo y ventas ====================== */
IF OBJECT_ID('dbo.vehiculos', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.vehiculos (
        id             INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_vehiculos PRIMARY KEY,
        marca          VARCHAR(50)  NOT NULL,
        modelo         VARCHAR(80)  NOT NULL,
        anio           INT          NOT NULL,
        precio         NUMERIC(14,2) NOT NULL CONSTRAINT CK_vehiculos_precio CHECK (precio >= 0),
        estado         VARCHAR(20)  NOT NULL CONSTRAINT DF_vehiculos_estado DEFAULT 'disponible'
                       CONSTRAINT CK_vehiculos_estado CHECK (estado IN ('disponible','pendiente','vendido')),
        motor          VARCHAR(20)  NOT NULL
                       CONSTRAINT CK_vehiculos_motor CHECK (motor IN ('electrico','hibrido','combustion')),
        categoria      VARCHAR(30)  NOT NULL CONSTRAINT DF_vehiculos_categoria DEFAULT 'Sedan',
        emisiones_co2  NUMERIC(6,2) NOT NULL CONSTRAINT CK_vehiculos_co2 CHECK (emisiones_co2 >= 0),  -- g/km; 0 = eléctrico (HU-05)
        imagen_url     VARCHAR(300) NULL,
        solicitante_id INT NULL CONSTRAINT FK_vehiculos_solicitante REFERENCES dbo.usuarios(id)
    );
    CREATE INDEX IX_vehiculos_motor_marca ON dbo.vehiculos (motor, marca);   -- filtros del catálogo (RF-05)
    CREATE INDEX IX_vehiculos_solicitante ON dbo.vehiculos (solicitante_id);
END;
GO

IF OBJECT_ID('dbo.ventas', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.ventas (
        id           INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_ventas PRIMARY KEY,
        usuario_id   INT NOT NULL CONSTRAINT FK_ventas_usuario  REFERENCES dbo.usuarios(id),
        vehiculo_id  INT NOT NULL CONSTRAINT FK_ventas_vehiculo REFERENCES dbo.vehiculos(id)
                     CONSTRAINT UQ_ventas_vehiculo UNIQUE,          -- un vehículo no se vende dos veces (RF-09)
        precio_venta NUMERIC(14,2) NOT NULL,                         -- precio del momento
        fecha_venta  DATETIME NULL CONSTRAINT DF_ventas_fecha DEFAULT GETUTCDATE()
    );
    CREATE INDEX IX_ventas_usuario ON dbo.ventas (usuario_id);
END;
GO

IF OBJECT_ID('dbo.tokens_recuperacion', 'U') IS NULL
BEGIN
    CREATE TABLE dbo.tokens_recuperacion (
        id               INT IDENTITY(1,1) NOT NULL CONSTRAINT PK_tokens PRIMARY KEY,
        usuario_id       INT NOT NULL CONSTRAINT FK_tokens_usuario REFERENCES dbo.usuarios(id) ON DELETE CASCADE,
        token            VARCHAR(100) NOT NULL CONSTRAINT UQ_tokens_token UNIQUE,
        fecha_expiracion DATETIME NOT NULL                            -- 15 minutos (HU-07)
    );
END;
GO

/* ====================== PASO 4: verificación ====================== */
SELECT 'password_existe' AS comprobacion, CASE WHEN COL_LENGTH('dbo.usuarios','password') IS NULL THEN 'NO (correcto)' ELSE 'SI (revisar)' END AS resultado
UNION ALL SELECT 'tabla_vehiculos',  CASE WHEN OBJECT_ID('dbo.vehiculos','U')  IS NOT NULL THEN 'OK' ELSE 'FALTA' END
UNION ALL SELECT 'tabla_ventas',     CASE WHEN OBJECT_ID('dbo.ventas','U')     IS NOT NULL THEN 'OK' ELSE 'FALTA' END
UNION ALL SELECT 'tabla_tokens',     CASE WHEN OBJECT_ID('dbo.tokens_recuperacion','U') IS NOT NULL THEN 'OK' ELSE 'FALTA' END
UNION ALL SELECT 'usuarios_que_deben_restablecer_clave', CAST(COUNT(*) AS VARCHAR(10)) FROM dbo.usuarios WHERE password_hash IS NULL;
GO
