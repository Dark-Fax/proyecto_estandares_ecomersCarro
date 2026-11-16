from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, CSRFError
from dotenv import load_dotenv
import urllib.parse
import os

db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()  # RNF-02/seguridad: token CSRF obligatorio en todo POST

def create_app():
    app = Flask(__name__)
    # 1. Cargar las variables del .env
    load_dotenv()
    # RNF-02/seguridad: la clave de sesión sale del entorno, no del código
    app.secret_key = os.getenv('SECRET_KEY', 'dev-only-change-me')
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FORCE_HTTPS', '0') == '1'
    
    # 2. Leer credenciales de Azure desde el .env
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_NAME')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')
    
    # Driver: Azure suele usar el 17 o el 18.
    driver = 'ODBC Driver 17 for SQL Server'

    # 3. Armar la cadena de conexión para AZURE
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    
    params = urllib.parse.quote_plus(connection_string)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL') or f"mssql+pyodbc:///?odbc_connect={params}"  # DATABASE_URL permite SQLite en pruebas
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 



    # === Configuración para subir imágenes ===
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'img', 'noticias')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # crea la carpeta si no existe
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}


    #Inicializamos SQLAlchemy con Flask

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    @app.errorhandler(CSRFError)
    def csrf_invalido(e):
        return ("Formulario inválido o sesión expirada (CSRF). Recarga la página e inténtalo de nuevo.", 400)

    # Importar rutas
    from app.routes.main_routes import main 
    from app.routes.usuarios_routes import usuarios
    from app.routes.vehiculos_routes import vehiculos
    from app.routes.noticias_routes import noticias
    from app.routes.calculadora_routes import calculadora
    from app.routes.cuenta_routes import cuenta 
    from app.routes.mapa_routes import mapa  # <--- 1. AGREGAR ESTO (Importar)
    
    from app.models import vehiculo  # noqa: registra modelos
    from app.routes.catalogo_routes import catalogo
    app.register_blueprint(catalogo)
    app.register_blueprint(main)     
    app.register_blueprint(usuarios)   
    app.register_blueprint(vehiculos)
    app.register_blueprint(noticias)
    app.register_blueprint(calculadora)
    app.register_blueprint(cuenta)
    app.register_blueprint(mapa)         # <--- 2. AGREGAR ESTO (Registrar)

    return app



