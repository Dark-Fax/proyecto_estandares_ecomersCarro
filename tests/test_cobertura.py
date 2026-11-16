"""Pruebas adicionales para elevar la cobertura (CP-21..CP-40)."""
import os, re
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import pytest
from helpers import CsrfClient
from app import create_app, db
from app.models.usuario import Usuario
from app.models.noticia import Noticia
from app.seed import seed

@pytest.fixture
def c():
    app = create_app(); app.config["TESTING"] = True; app.test_client_class = CsrfClient
    with app.app_context():
        db.create_all(); seed(); yield app.test_client(); db.drop_all()

def reg(c, u="ana", p="Clave1234"):
    c.post("/register", data={"usuario": u, "email": f"{u}@x.com", "password": p, "telefono": "3001112233"})
    return c.post("/login", data={"usuario": u, "password": p})

def adm(c): return c.post("/login", data={"usuario": "admin", "password": "Admin1234"})

def test_cp21_bcrypt_formato(c):
    reg(c); assert Usuario.query.filter_by(nombre="ana").first().password_hash.startswith("$2b$10$")

def test_cp22_check_password_sin_hash(c):
    assert Usuario(nombre="z", email="z@z", telefono="1").check_password("x") is False
    assert Usuario(nombre="z", email="z@z", telefono="1", password_hash="no-es-bcrypt").check_password("x") is False

def test_cp23_registro_campos_vacios_y_correo_duplicado(c):
    c.post("/register", data={"usuario": "", "email": "", "password": "", "telefono": ""})
    reg(c); r = c.post("/register", data={"usuario": "otro", "email": "ana@x.com", "password": "Clave1234", "telefono": "1"})
    assert Usuario.query.count() == 2 and r.status_code == 302
    assert c.get("/register").status_code == 200 and c.get("/login").status_code == 200

def test_cp24_home_y_dashboard(c):
    assert c.get("/").status_code == 302 and c.get("/dashboard").status_code == 302
    reg(c); assert c.get("/").status_code == 302

def test_cp25_cuenta(c):
    assert c.get("/cuenta").status_code == 302 and c.post("/cuenta/editar").status_code == 302
    reg(c); assert c.get("/cuenta").status_code == 200
    c.post("/cuenta/editar", data={"nombre": "ana", "telefono": "3009998877", "email": "ana@x.com", "nueva_contrasena": "Nueva1234"})
    assert Usuario.query.filter_by(nombre="ana").first().check_password("Nueva1234")
    c.post("/cuenta/editar", data={"nombre": "ana", "telefono": "1", "email": "ana@x.com"})

def test_cp26_eliminar_cuenta(c):
    assert c.post("/cuenta/eliminar").status_code == 302
    reg(c); c.post("/cuenta/eliminar"); assert Usuario.query.filter_by(nombre="ana").first() is None

def test_cp27_calculadora(c):
    reg(c); assert c.get("/calculadora/").status_code == 200
    assert c.post("/calculadora/calcular", data={"autonomia": "400", "distancia": "900", "km_carga": "160", "min_carga": "30"}).status_code == 200
    assert c.post("/calculadora/calcular", data={"autonomia": "400"}).status_code == 200
    assert c.post("/calculadora/calcular", data={"autonomia": "abc"}).status_code == 302

def test_cp28_calculadora_sin_sesion(c):
    assert c.post("/calculadora/calcular", data={"autonomia": "4"}).status_code == 302

def test_cp29_mapa(c, monkeypatch):
    class R:
        status_code = 200; text = "[]"
        def json(self): return []
    class Mala(R):
        def json(self): raise ValueError("x")
    assert c.get("/mapa/").status_code == 302
    reg(c)
    monkeypatch.setattr("app.routes.mapa_routes.requests.get", lambda *a, **k: R())
    assert c.get("/mapa/").status_code == 200
    monkeypatch.setattr("app.routes.mapa_routes.requests.get", lambda *a, **k: Mala())
    assert c.get("/mapa/").status_code == 200

def test_cp30_vehiculos_redirigen_al_catalogo(c):
    """Las 6 rutas estáticas duplicadas redirigen al catálogo dinámico, con o sin sesión."""
    esperado = {"kia": "Kia", "bmw": "BMW", "bolt": "Chevrolet", "leaf": "Nissan", "volvo": "Volvo", "tesla": "Tesla"}
    for sesion in (False, True):
        if sesion: reg(c)
        for ruta, marca in esperado.items():
            r = c.get(f"/vehiculos/{ruta}")
            assert r.status_code == 302 and f"/catalogo/?marca={marca}" in r.location
    assert c.get("/vehiculos/listar").status_code == 200  # con sesión activa
    assert marca in c.get(f"/vehiculos/tesla", follow_redirects=True).get_data(as_text=True)

def test_cp31_noticias_crud_admin(c):
    adm(c)
    assert c.get("/noticias/inicio").status_code == 200
    assert c.get("/noticias/crear_formulario").status_code == 200
    r = c.post("/noticias/crear_formulario", data={"titulo": "T", "categoria": "C", "contenido": "X", "vistas": "0"}, content_type="multipart/form-data")
    assert r.status_code == 302 and Noticia.query.count() == 1
    assert c.get("/noticias/listar").status_code == 200
    assert c.get("/noticias/ver/1").status_code == 200
    assert c.get("/noticias/editar/1").status_code == 200
    c.post("/noticias/editar/1", data={"titulo": "T2", "categoria": "C", "contenido": "Y", "vistas": "3"}, content_type="multipart/form-data")
    assert db.session.get(Noticia, 1).titulo == "T2"
    for _ in range(2): c.post("/noticias/crear_formulario", data={"titulo": "N", "categoria": "C", "contenido": "X"}, content_type="multipart/form-data")
    c.post("/noticias/eliminar/1"); assert Noticia.query.count() == 3  # ids 1 y 2 son noticias de prueba protegidas
    c.post("/noticias/eliminar/3"); assert Noticia.query.count() == 2

def test_cp32_noticias_cliente_y_sin_sesion(c):
    assert c.get("/noticias/listar").status_code == 302
    reg(c); assert c.get("/noticias/listar").status_code == 200
    assert c.post("/noticias/eliminar/1").status_code == 302

def test_cp33_admin_inventario_crud(c):
    adm(c)
    assert c.get("/catalogo/admin/inventario").status_code == 200
    assert c.get("/catalogo/admin/vehiculo").status_code == 200
    d = {"marca": "BYD", "modelo": "Dolphin", "anio": 2024, "precio": 99000000, "motor": "electrico", "categoria": "Hatchback", "emisiones_co2": 0, "imagen_url": ""}
    c.post("/catalogo/admin/vehiculo", data=d)
    from app.models.vehiculo import Vehiculo
    v = Vehiculo.query.filter_by(marca="BYD").first(); assert v is not None
    assert c.get(f"/catalogo/admin/vehiculo/{v.id}").status_code == 200
    c.post(f"/catalogo/admin/vehiculo/{v.id}", data={**d, "modelo": "Seal"}); assert db.session.get(Vehiculo, v.id).modelo == "Seal"
    c.post(f"/catalogo/admin/vehiculo/{v.id}/eliminar"); assert db.session.get(Vehiculo, v.id) is None

def test_cp34_admin_usuarios(c):
    reg(c); c.get("/logout"); adm(c)
    assert c.get("/catalogo/admin/usuarios").status_code == 200
    u = Usuario.query.filter_by(nombre="ana").first()
    c.post(f"/catalogo/admin/usuarios/{u.id}/rol", data={"rol": "admin"}); assert db.session.get(Usuario, u.id).rol == "admin"
    c.post(f"/catalogo/admin/usuarios/{u.id}/rol", data={"rol": "usuario"})
    c.post("/catalogo/admin/usuarios/1/eliminar")  # no puede eliminarse a sí mismo
    assert Usuario.query.filter_by(nombre="admin").first() is not None
    c.post(f"/catalogo/admin/usuarios/{u.id}/eliminar"); assert db.session.get(Usuario, u.id) is None

def test_cp35_historial_y_dashboard(c):
    reg(c); c.post("/catalogo/1/solicitar"); c.post("/catalogo/2/solicitar"); c.get("/logout")
    adm(c); c.post("/catalogo/admin/ventas/registrar/1"); c.post("/catalogo/admin/ventas/registrar/9")  # 9 sin solicitante
    assert c.get("/catalogo/ventas").status_code == 200
    r = c.get("/catalogo/admin/dashboard"); assert r.status_code == 200 and b"100.0%" in r.data
    c.get("/logout"); reg(c, "beto"); assert c.get("/catalogo/ventas").status_code == 200
    assert c.get("/catalogo/ventas/1/comprobante.pdf").status_code == 403

def test_cp36_detalle_y_paginacion(c):
    assert c.get("/catalogo/1").status_code == 200 and c.get("/catalogo/999").status_code == 404
    assert c.get("/catalogo/?pagina=1&modelo=EV6&precio_max=900000000&anio=2024&categoria=SUV").status_code == 200

def test_cp37_solicitar_no_disponible(c):
    reg(c); c.post("/catalogo/1/solicitar"); r = c.post("/catalogo/1/solicitar", follow_redirects=True)
    assert "ya no está disponible" in r.get_data(as_text=True)

def test_cp38_recuperar_token_invalido_y_clave_debil(c):
    assert c.get("/catalogo/recuperar").status_code == 200
    c.post("/catalogo/recuperar", data={"email": "noexiste@x.com"})
    assert c.get("/catalogo/restablecer/falso").status_code == 302
    reg(c); r = c.post("/catalogo/recuperar", data={"email": "ana@x.com"}, follow_redirects=True)
    t = re.search(r"/restablecer/([\w-]+)", r.get_data(as_text=True)).group(1)
    assert c.get(f"/catalogo/restablecer/{t}").status_code == 200
    c.post(f"/catalogo/restablecer/{t}", data={"password": "debil"})
    assert Usuario.query.filter_by(nombre="ana").first().check_password("Clave1234")

def test_cp39_token_expirado(c):
    from datetime import datetime, timedelta
    from app.models.vehiculo import TokenRecuperacion
    reg(c); u = Usuario.query.filter_by(nombre="ana").first()
    db.session.add(TokenRecuperacion(usuario_id=u.id, token="viejo", fecha_expiracion=datetime.utcnow() - timedelta(minutes=1))); db.session.commit()
    assert c.get("/catalogo/restablecer/viejo").status_code == 302

def test_cp40_modelos_repr_y_ecologico(c):
    from app.models.vehiculo import Vehiculo
    assert "ana" in repr(Usuario(nombre="x", email="ana@x.com", telefono="1"))
    assert Vehiculo.query.filter_by(motor="combustion").first().es_ecologico() is False
