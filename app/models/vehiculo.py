from datetime import datetime
from app import db
from app.imagenes import foto_de

ECOLOGICOS = ("electrico", "hibrido")

class Vehiculo(db.Model):
    __tablename__ = "vehiculos"
    id = db.Column(db.Integer, primary_key=True)
    marca = db.Column(db.String(50), nullable=False)
    modelo = db.Column(db.String(80), nullable=False)
    anio = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Numeric(14, 2), nullable=False)
    estado = db.Column(db.String(20), nullable=False, default="disponible")  # disponible|pendiente|vendido
    motor = db.Column(db.String(20), nullable=False)  # electrico|hibrido|combustion
    categoria = db.Column(db.String(30), nullable=False, default="Sedan")
    emisiones_co2 = db.Column(db.Numeric(6, 2), nullable=False)  # g/km, 0 = electrico
    imagen_url = db.Column(db.String(300))
    solicitante_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    __table_args__ = (db.Index("IX_vehiculos_motor_marca", "motor", "marca"),)  # filtros del catálogo (RF-05)

    def es_ecologico(self):  # RF-04: distintivo Planeta Verde
        return self.motor in ECOLOGICOS

    @property
    def foto(self):
        """Foto a mostrar: la de la base de datos o, si está vacía, la de referencia del catálogo."""
        return self.imagen_url or foto_de(self.marca, self.modelo)

    @property
    def carroceria(self):
        """Tipo de silueta (sedan | suv | hatch) según la categoría, para la imagen de reserva."""
        c = (self.categoria or "").lower()
        return "suv" if "suv" in c else "hatch" if ("hatch" in c or "compact" in c) else "sedan"

class Venta(db.Model):
    __tablename__ = "ventas"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    vehiculo_id = db.Column(db.Integer, db.ForeignKey("vehiculos.id"), unique=True, nullable=False)
    precio_venta = db.Column(db.Numeric(14, 2), nullable=False)
    fecha_venta = db.Column(db.DateTime, default=datetime.utcnow)
    usuario = db.relationship("Usuario")
    vehiculo = db.relationship("Vehiculo")

class TokenRecuperacion(db.Model):
    __tablename__ = "tokens_recuperacion"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
