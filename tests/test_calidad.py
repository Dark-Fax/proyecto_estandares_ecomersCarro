"""Pruebas automatizadas - Estándares y Métricas (CP-01..CP-10)."""
import os, pytest
from helpers import CsrfClient
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
from app import create_app, db
from app.models.usuario import Usuario

@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    app.test_client_class = CsrfClient
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def reg(c, u="ana", e="ana@correo.com", p="Clave1234", t="3001234567"):
    return c.post("/register", data={"usuario": u, "email": e, "password": p, "telefono": t})

def login(c, u="ana", p="Clave1234"):
    return c.post("/login", data={"usuario": u, "password": p})

def test_cp01_registro_exitoso(client):
    r = reg(client); assert r.status_code == 302 and Usuario.query.count() == 1

def test_cp02_registro_duplicado(client):
    reg(client); reg(client); assert Usuario.query.count() == 1

def test_cp03_login_correcto(client):
    reg(client); login(client)
    with client.session_transaction() as s: assert s["usuario_nombre"] == "ana"

def test_cp04_login_incorrecto(client):
    reg(client); login(client, p="mala")
    with client.session_transaction() as s: assert "usuario_id" not in s

def test_cp05_ruta_protegida_sin_sesion(client):
    r = client.get("/vehiculos/listar"); assert r.status_code == 302 and "/login" in r.location

def test_cp06_ruta_protegida_con_sesion(client):
    reg(client); login(client); assert client.get("/vehiculos/listar").status_code == 200

def test_cp07_rnf01_password_hasheada(client):
    reg(client); u = Usuario.query.first()
    assert u.password_hash and "Clave1234" not in u.password_hash

def test_cp08_admin_required(client):
    reg(client); login(client)
    r = client.get("/noticias/crear_formulario"); assert r.status_code == 302

def test_cp09_logout(client):
    reg(client); login(client); client.get("/logout")
    with client.session_transaction() as s: assert "usuario_id" not in s

def test_cp10_calculadora_requiere_sesion(client):
    assert client.get("/calculadora/").status_code == 302

# ---- Núcleo de compraventa (CP-11..CP-20) ----
from app.models.vehiculo import Vehiculo, Venta
from app.seed import seed

def admin_login(c):
    seed(); return c.post("/login", data={"usuario": "admin", "password": "Admin1234"})

def test_cp11_catalogo_publico_con_distintivo(client):
    seed(); r = client.get("/catalogo/"); assert r.status_code == 200 and b"Planeta Verde" in r.data

def test_cp12_filtro_motor_y_vacio(client):
    seed()
    assert b"CX-5" not in client.get("/catalogo/?motor=electrico").data
    assert "No hay veh" in client.get("/catalogo/?marca=Inexistente").get_data(as_text=True)

def test_cp13_solicitar_sin_sesion(client):
    seed(); assert client.post("/catalogo/1/solicitar").status_code == 302

def test_cp14_solicitar_cambia_a_pendiente(client):
    seed(); reg(client); login(client); client.post("/catalogo/1/solicitar")
    assert db.session.get(Vehiculo, 1).estado == "pendiente"

def test_cp15_venta_admin_y_no_duplicada(client):
    seed(); reg(client); login(client); client.post("/catalogo/1/solicitar"); client.get("/logout")
    admin_login(client); client.post("/catalogo/admin/ventas/registrar/1"); client.post("/catalogo/admin/ventas/registrar/1")
    assert Venta.query.count() == 1 and db.session.get(Vehiculo, 1).estado == "vendido"

def test_cp16_cliente_no_registra_venta(client):
    seed(); reg(client); login(client); client.post("/catalogo/1/solicitar")
    assert client.post("/catalogo/admin/ventas/registrar/1").status_code == 302 and Venta.query.count() == 0

def test_cp17_comprobante_pdf(client):
    seed(); reg(client); login(client); client.post("/catalogo/1/solicitar"); client.get("/logout")
    admin_login(client); client.post("/catalogo/admin/ventas/registrar/1")
    r = client.get("/catalogo/ventas/1/comprobante.pdf"); assert r.data.startswith(b"%PDF")

def test_cp18_no_eliminar_con_ventas_y_co2_obligatorio(client):
    seed(); reg(client); login(client); client.post("/catalogo/1/solicitar"); client.get("/logout")
    admin_login(client); client.post("/catalogo/admin/ventas/registrar/1"); client.post("/catalogo/admin/vehiculo/1/eliminar")
    assert db.session.get(Vehiculo, 1) is not None
    client.post("/catalogo/admin/vehiculo", data={"marca":"X","modelo":"Y","anio":2024,"precio":1,"motor":"electrico","categoria":"SUV"})
    assert Vehiculo.query.count() == 10

def test_cp19_recuperar_contrasena(client):
    reg(client); client.post("/catalogo/recuperar", data={"email": "ana@correo.com"})
    from app.models.vehiculo import TokenRecuperacion
    t = TokenRecuperacion.query.first().token
    client.post(f"/catalogo/restablecer/{t}", data={"password": "Nueva1234"}); client.get("/logout")
    login(client, p="Nueva1234")
    with client.session_transaction() as s: assert "usuario_id" in s

def test_cp20_dashboard_solo_admin(client):
    seed(); reg(client); login(client); assert client.get("/catalogo/admin/dashboard").status_code == 302
