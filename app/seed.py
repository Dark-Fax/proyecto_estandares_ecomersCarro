"""Datos iniciales: admin y catálogo Planeta Verde. Uso: python -m flask --app run seed  (o desde run.py)."""
import os
from app import db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo

VEHICULOS = [
 ("Tesla","Model 3 Long Range",2024,320000000,"electrico","Sedan",0),
 ("Kia","EV6",2024,245000000,"electrico","SUV",0),
 ("BMW","i4",2024,330000000,"electrico","Sedan",0),
 ("Chevrolet","Bolt EV",2023,150000000,"electrico","Hatchback",0),
 ("Nissan","Leaf",2023,140000000,"electrico","Hatchback",0),
 ("Volvo","XC40 Recharge",2024,280000000,"electrico","SUV",0),
 ("Toyota","Corolla Hybrid",2024,135000000,"hibrido","Sedan",98),
 ("Kia","Niro Hybrid",2023,150000000,"hibrido","SUV",101),
 ("Mazda","CX-5",2023,125000000,"combustion","SUV",178),
 ("Renault","Duster",2022,90000000,"combustion","SUV",160),
]

def seed():
    if not Usuario.query.filter_by(nombre="admin").first():
        a = Usuario(nombre="admin", email="admin@planetaverde.co", telefono="3000000000", rol="admin")
        a.set_password(os.getenv("ADMIN_PASSWORD", "Admin1234")); db.session.add(a)
    if Vehiculo.query.count() == 0:
        for m,mo,an,pr,mt,ca,co in VEHICULOS:
            db.session.add(Vehiculo(marca=m,modelo=mo,anio=an,precio=pr,motor=mt,categoria=ca,emisiones_co2=co))
    db.session.commit()
