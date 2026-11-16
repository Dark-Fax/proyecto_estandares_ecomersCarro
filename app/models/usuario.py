from app import db
import bcrypt

#Modelo de ejemplo 
class Usuario(db.Model): #Definimos una clase llamada 'Usuario',
    #que heredara de db.Model y hara un mapeo con una tabla de la DB
    __tablename__ = 'usuarios'


    #Definimos un id con formato Integer el cual sera su llave primaria [PK]
    id = db.Column(db.Integer, primary_key=True)
    #nombre que sera un String de longitud 100 y que no puede ser null
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    #email que sera un String de longitud 70 y que no puede ser null, ademas de ser unico
    email = db.Column(db.String(70), unique=True, nullable=False)
    #password que sera un String de longitud 50 y que no puede ser null
    password_hash = db.Column(db.String(512), nullable=True)
    #telefono que sera un String de longitud 10 y que no puede ser null
    telefono = db.Column(db.String(10), nullable=False)

    #Nuevo, rol de usuario (admin o usuario)    -----> nueva agregacion  
    rol = db.Column(db.String(50), nullable=False, default="usuario")

    # ✅ Guardar la contraseña encriptada
    def set_password(self, password):
        # RNF-01: Bcrypt, costo 10 (hash con sal; inicia con $2b$10$)
        self.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=10)).decode()

    # ✅ Verificar contraseña (durante login)
    def check_password(self, password):
        if not self.password_hash:
            return False
        try:
            return bcrypt.checkpw(password.encode(), self.password_hash.encode())
        except ValueError:
            return False


    def __repr__(self):
        return f"<Usuario {self.email}>"