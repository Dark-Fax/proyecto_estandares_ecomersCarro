#!/usr/bin/env python3
"""Deja la base lista para grabar el video de demostración (idempotente).

Crea los clientes `ana` y `luis` (contraseña Clave1234) y 4 ventas previas (2 eléctricos, 1 híbrido,
1 de combustión) para que el dashboard ambiental muestre datos. Deja libres el Kia EV6 y el BMW i4
para la demostración en vivo. Uso:  python scripts/preparar_demo.py   (usa DATABASE_URL o Azure SQL del .env)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import create_app, db
from app.seed import seed
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo, Venta

VENTAS_PREVIAS = [("Chevrolet", "ana"), ("Nissan", "ana"), ("Toyota", "luis"), ("Mazda", "luis")]


def main():
    app = create_app()
    with app.app_context():
        db.create_all(); seed()
        for nombre in ("ana", "luis"):
            if not Usuario.query.filter_by(nombre=nombre).first():
                u = Usuario(nombre=nombre, email=f"{nombre}@correo.com", telefono="3001112233")
                u.set_password("Clave1234"); db.session.add(u)
        db.session.commit()
        for marca, nombre in VENTAS_PREVIAS:
            v, u = Vehiculo.query.filter_by(marca=marca).first(), Usuario.query.filter_by(nombre=nombre).first()
            if v and v.estado == "disponible":
                v.estado, v.solicitante_id = "vendido", u.id
                db.session.add(Venta(usuario_id=u.id, vehiculo_id=v.id, precio_venta=v.precio))
        db.session.commit()
        print(f"Demo lista: {Vehiculo.query.count()} vehículos, {Venta.query.count()} ventas, {Usuario.query.count()} usuarios.")


if __name__ == "__main__":
    main()
