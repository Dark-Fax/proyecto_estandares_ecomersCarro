"""Fotos del catálogo: todos los vehículos muestran imagen (la del dato o la de referencia)."""
import os, pytest
from helpers import CsrfClient
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from app import create_app, db
from app.models.vehiculo import Vehiculo
from app.seed import seed
from app.imagenes import FOTOS


@pytest.fixture
def client():
    app = create_app(); app.config["TESTING"] = True; app.test_client_class = CsrfClient
    with app.app_context():
        db.create_all(); yield app.test_client(); db.drop_all()


def test_seed_nuevo_guarda_foto_de_cada_vehiculo(client):
    seed(); assert Vehiculo.query.count() == 10 and all(v.imagen_url for v in Vehiculo.query.all())


def test_seed_completa_fotos_vacias_sin_pisar_las_existentes(client):
    seed()
    a, b = Vehiculo.query.filter_by(modelo="CX-5").one(), Vehiculo.query.filter_by(modelo="EV6").one()
    a.imagen_url = ""; b.imagen_url = "https://ejemplo.com/propia.jpg"; db.session.commit()
    seed()
    assert Vehiculo.query.filter_by(modelo="CX-5").one().imagen_url == FOTOS[("Mazda", "CX-5")]
    assert Vehiculo.query.filter_by(modelo="EV6").one().imagen_url == "https://ejemplo.com/propia.jpg"


def test_catalogo_muestra_imagen_aunque_la_base_este_vacia(client):
    seed(); Vehiculo.query.update({"imagen_url": None}); db.session.commit()
    html = client.get("/catalogo/").get_data(as_text=True)
    assert html.count("<img ") == 10 and "Silueta de vehículo" in html


def test_carroceria_para_la_silueta_de_reserva(client):
    seed(); c = {v.modelo: v.carroceria for v in Vehiculo.query.all()}
    assert c["EV6"] == "suv" and c["Bolt EV"] == "hatch" and c["i4"] == "sedan"
