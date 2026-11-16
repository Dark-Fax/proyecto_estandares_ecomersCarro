"""Pruebas de las mejoras del segundo corte (CP-41..CP-62 y CP-68..CP-70): CSRF, SMTP, navegación, decoradores y robustez."""
import glob, os, re
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import pytest
from helpers import CsrfClient
from app import create_app, db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo, Venta, TokenRecuperacion
from app.seed import seed


@pytest.fixture
def c():
    app = create_app(); app.config["TESTING"] = True; app.test_client_class = CsrfClient
    with app.app_context():
        db.create_all(); seed(); yield app.test_client(); db.drop_all()


def reg(c, u="ana"):
    c.post("/register", data={"usuario": u, "email": f"{u}@x.com", "password": "Clave1234", "telefono": "3001112233"})
    return c.post("/login", data={"usuario": u, "password": "Clave1234"})

def adm(c): return c.post("/login", data={"usuario": "admin", "password": "Admin1234"})


# ---------------------------------------------------------------- CSRF (tarea 1)
POSTS = ["/login", "/register", "/catalogo/recuperar", "/catalogo/restablecer/x", "/catalogo/1/solicitar",
         "/catalogo/admin/ventas/registrar/1", "/catalogo/admin/vehiculo", "/catalogo/admin/vehiculo/1",
         "/catalogo/admin/vehiculo/1/eliminar", "/catalogo/admin/usuarios/1/rol", "/catalogo/admin/usuarios/1/eliminar",
         "/calculadora/calcular", "/cuenta/editar", "/cuenta/eliminar", "/noticias/crear_formulario",
         "/noticias/editar/1", "/noticias/eliminar/3"]

def test_cp41_post_sin_token_es_rechazado(c):
    c.auto_csrf = False
    for url in POSTS:
        assert c.post(url, data={}).status_code == 400, url

def test_cp42_token_invalido_rechazado_y_valido_aceptado(c):
    c.auto_csrf = False
    assert c.post("/login", data={"usuario": "admin", "password": "Admin1234", "csrf_token": "falso"}).status_code == 400
    token = c.token()
    r = c.post("/login", data={"usuario": "admin", "password": "Admin1234", "csrf_token": token})
    assert r.status_code == 302 and "/noticias/inicio" in r.location
    assert "protegido" not in c.post("/login", data={}).get_data(as_text=True) and "CSRF" in c.post("/login", data={}).get_data(as_text=True)

def test_cp43_todos_los_formularios_post_llevan_token():
    n = 0
    for f in glob.glob("app/templates/**/*.html", recursive=True):
        html = open(f, encoding="utf-8").read()
        for form in re.finditer(r"<form\b[^>]*>", html, re.I):
            if re.search(r'method\s*=\s*["\']?post', form.group(0), re.I):
                n += 1
                assert 'name="csrf_token"' in html[form.end():form.end() + 120], f"{f}: formulario sin token"
    assert n == 16  # 16 formularios POST en las plantillas

def test_cp44_get_no_exige_token_y_cookie_httponly(c):
    c.auto_csrf = False
    r = c.get("/catalogo/?motor=electrico"); assert r.status_code == 200
    assert "HttpOnly" in c.get("/login").headers["Set-Cookie"]


# ---------------------------------------------------------------- SMTP (tarea 2)
class FakeSMTP:
    instancias = []
    def __init__(self, host, port, timeout=None):
        self.host, self.port, self.log, self.msg, self.cred = host, port, [], None, None
        FakeSMTP.instancias.append(self)
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def starttls(self): self.log.append("starttls")
    def login(self, u, p): self.cred = (u, p)
    def send_message(self, m): self.msg = m

@pytest.fixture
def smtp(monkeypatch):
    FakeSMTP.instancias = []
    monkeypatch.setattr("app.utils.correo.smtplib.SMTP", FakeSMTP)
    monkeypatch.setattr("app.utils.correo.smtplib.SMTP_SSL", FakeSMTP)
    monkeypatch.setenv("MAIL_SERVER", "smtp.ejemplo.com"); monkeypatch.setenv("MAIL_USER", "no-reply@planetaverde.co")
    monkeypatch.setenv("MAIL_PASS", "secreto")
    return FakeSMTP

def test_cp45_recuperar_envia_correo_y_no_muestra_enlace(c, smtp):
    reg(c); r = c.post("/catalogo/recuperar", data={"email": "ana@x.com"})
    t = TokenRecuperacion.query.first().token
    assert t not in r.get_data(as_text=True) and "se envió un enlace" in r.get_data(as_text=True)
    s = smtp.instancias[0]
    assert (s.host, s.port, s.log, s.cred) == ("smtp.ejemplo.com", 587, ["starttls"], ("no-reply@planetaverde.co", "secreto"))
    assert s.msg["To"] == "ana@x.com" and f"/catalogo/restablecer/{t}" in s.msg.get_content() and "15 minutos" in s.msg.get_content()

def test_cp46_puerto_465_usa_ssl_sin_starttls(c, smtp, monkeypatch):
    monkeypatch.setenv("MAIL_PORT", "465"); monkeypatch.setenv("MAIL_FROM", "Planeta Verde <pv@x.co>")
    reg(c); c.post("/catalogo/recuperar", data={"email": "ana@x.com"})
    s = smtp.instancias[0]; assert s.port == 465 and s.log == [] and s.msg["From"] == "Planeta Verde <pv@x.co>"

def test_cp47_fallo_smtp_informa_y_no_filtra_enlace(c, smtp, monkeypatch):
    import smtplib
    def boom(self, m): raise smtplib.SMTPException("caído")
    monkeypatch.setattr(FakeSMTP, "send_message", boom)
    reg(c); r = c.post("/catalogo/recuperar", data={"email": "ana@x.com"}); html = r.get_data(as_text=True)
    assert "No fue posible enviar" in html and TokenRecuperacion.query.first().token not in html

def test_cp48_correo_inexistente_no_envia(c, smtp):
    r = c.post("/catalogo/recuperar", data={"email": "nadie@x.com"})
    assert smtp.instancias == [] and "se envió un enlace" in r.get_data(as_text=True) and TokenRecuperacion.query.count() == 0

def test_cp49_configuracion_incompleta_mantiene_modo_desarrollo(c, monkeypatch):
    monkeypatch.setenv("MAIL_SERVER", "smtp.ejemplo.com")  # faltan MAIL_USER y MAIL_PASS
    reg(c); r = c.post("/catalogo/recuperar", data={"email": "ana@x.com"})
    assert "modo desarrollo" in r.get_data(as_text=True) and "/catalogo/restablecer/" in r.get_data(as_text=True)

def test_cp50_enviar_sin_configurar_devuelve_false():
    from app.utils.correo import enviar_enlace_recuperacion, smtp_configurado
    assert smtp_configurado() is False and enviar_enlace_recuperacion("a@a.com", "http://x") is False


# ---------------------------------------------------------------- Navegación (tarea 3)
def test_cp51_menu_enlaza_catalogo_y_oculta_admin_a_clientes(c):
    reg(c); html = c.get("/calculadora/").get_data(as_text=True)  # incluye sidebar y header
    assert html.count('href="/catalogo/"') >= 2  # sidebar y header_usuario
    assert "/catalogo/ventas" in html
    for ruta in ("/catalogo/admin/inventario", "/catalogo/admin/usuarios", "/catalogo/admin/dashboard"):
        assert ruta not in html

def test_cp52_menu_admin_muestra_enlaces_de_administracion(c):
    adm(c); html = c.get("/calculadora/").get_data(as_text=True)
    for ruta in ("/catalogo/admin/inventario", "/catalogo/admin/usuarios", "/catalogo/admin/dashboard"):
        assert html.count(ruta) >= 2, ruta  # sidebar y header

def test_cp53_catalogo_enlaza_de_vuelta_al_resto_del_sitio(c):
    reg(c); html = c.get("/catalogo/").get_data(as_text=True)
    for ruta in ("/noticias/inicio", "/calculadora/", "/mapa/", "/cuenta"):
        assert ruta in html
    c.get("/logout"); assert "/mapa/" not in c.get("/catalogo/").get_data(as_text=True)


# ---------------------------------------------------------------- Decoradores compartidos (tarea 4)
RUTAS_PROTEGIDAS = ["/calculadora/", "/mapa/", "/cuenta", "/noticias/inicio", "/noticias/listar", "/noticias/ver/1",
                    "/vehiculos/listar", "/catalogo/ventas", "/catalogo/ventas/1/comprobante.pdf",
                    "/catalogo/admin/inventario", "/catalogo/admin/usuarios", "/catalogo/admin/dashboard", "/dashboard"]

def test_cp54_rutas_protegidas_redirigen_a_login(c):
    for url in RUTAS_PROTEGIDAS:
        r = c.get(url); assert r.status_code == 302 and "/login" in r.location, url

def test_cp55_admin_required_destino_por_modulo(c):
    reg(c)
    assert "/catalogo/" in c.get("/catalogo/admin/inventario").location          # destino por defecto
    assert "/noticias/listar" in c.get("/noticias/crear_formulario").location      # destino="noticias.listar"
    assert "/noticias/listar" in c.get("/noticias/editar/1").location

def test_cp56_decoradores_conservan_metadatos():
    from app.routes.catalogo_routes import dashboard
    from app.routes.noticias_routes import crear_formulario
    from app.utils.auth import admin_required, login_required
    assert dashboard.__name__ == "dashboard" and crear_formulario.__name__ == "crear_formulario"
    @admin_required
    def a(): "doc-a"
    @login_required
    def b(): "doc-b"
    assert (a.__name__, a.__doc__, b.__name__, b.__doc__) == ("a", "doc-a", "b", "doc-b")

def test_cp57_un_solo_origen_de_decoradores():
    for f in glob.glob("app/routes/*.py"):
        assert "def login_required" not in open(f, encoding="utf-8").read(), f
        assert "def admin_required" not in open(f, encoding="utf-8").read(), f


# ---------------------------------------------------------------- Robustez (hallazgos adicionales)
def test_cp58_eliminar_cuenta_libera_solicitud_con_fk_activa(c):
    reg(c); c.post("/catalogo/1/solicitar"); c.post("/catalogo/recuperar", data={"email": "ana@x.com"})  # deja un token
    db.session.execute(db.text("PRAGMA foreign_keys=ON")); db.session.commit()  # como Azure SQL: la FK se exige
    c.post("/cuenta/eliminar")
    v = db.session.get(Vehiculo, 1)
    assert Usuario.query.filter_by(nombre="ana").first() is None and v.estado == "disponible" and v.solicitante_id is None
    assert TokenRecuperacion.query.count() == 0

def test_cp59_no_se_elimina_cuenta_con_compras(c):
    reg(c); c.post("/catalogo/1/solicitar"); c.get("/logout"); adm(c)
    c.post("/catalogo/admin/ventas/registrar/1"); c.get("/logout"); c.post("/login", data={"usuario": "ana", "password": "Clave1234"})
    r = c.post("/cuenta/eliminar", follow_redirects=True)
    assert Usuario.query.filter_by(nombre="ana").first() is not None and "compras registradas" in r.get_data(as_text=True)

def test_cp60_admin_elimina_usuario_con_solicitud_pendiente(c):
    reg(c); c.post("/catalogo/2/solicitar"); c.post("/catalogo/recuperar", data={"email": "ana@x.com"}); c.get("/logout"); adm(c)
    uid = Usuario.query.filter_by(nombre="ana").first().id
    db.session.execute(db.text("PRAGMA foreign_keys=ON")); db.session.commit()
    c.post(f"/catalogo/admin/usuarios/{uid}/eliminar")
    assert db.session.get(Usuario, uid) is None and db.session.get(Vehiculo, 2).estado == "disponible"

def test_cp61_dashboard_raiz_redirige_segun_rol(c):
    reg(c); assert "/noticias/inicio" in c.get("/dashboard").location
    c.get("/logout"); adm(c); assert "/catalogo/admin/dashboard" in c.get("/dashboard").location

def test_cp62_mapa_tolera_api_caida(c, monkeypatch):
    import requests
    def caida(*a, **k): raise requests.ConnectionError("sin red")
    monkeypatch.setattr("app.routes.mapa_routes.requests.get", caida)
    reg(c); assert c.get("/mapa/").status_code == 200


# ---------------------------------------------------------------- Subida de imágenes de noticias
import io

@pytest.fixture
def cn(c, tmp_path):
    c.application.config["UPLOAD_FOLDER"] = str(tmp_path)  # las pruebas no escriben en static/
    adm(c); return c

def _datos(imagen=None, **extra):
    d = {"titulo": "T", "categoria": "C", "contenido": "X", **extra}
    if imagen: d["imagen"] = imagen
    return d

def test_cp68_crear_noticia_con_imagen_valida(cn, tmp_path):
    r = cn.post("/noticias/crear_formulario", data=_datos((io.BytesIO(b"\x89PNG"), "foto nueva.png")), content_type="multipart/form-data")
    from app.models.noticia import Noticia
    n = Noticia.query.first(); assert r.status_code == 302 and n.imagen == "foto_nueva.png" and (tmp_path / "foto_nueva.png").exists()

def test_cp69_formato_no_permitido_no_guarda_archivo(cn, tmp_path):
    from app.models.noticia import Noticia
    r = cn.post("/noticias/crear_formulario", data=_datos((io.BytesIO(b"MZ"), "virus.exe")), content_type="multipart/form-data", follow_redirects=True)
    assert Noticia.query.first().imagen is None and list(tmp_path.iterdir()) == []
    assert "Formato de imagen no permitido" in r.get_data(as_text=True)

def test_cp70_editar_noticia_imagen_valida_invalida_y_sin_extension(cn, tmp_path):
    from app.models.noticia import Noticia
    cn.post("/noticias/crear_formulario", data=_datos(), content_type="multipart/form-data")
    nid = Noticia.query.first().id
    cn.post(f"/noticias/editar/{nid}", data=_datos((io.BytesIO(b"x"), "a.jpg")), content_type="multipart/form-data")
    assert db.session.get(Noticia, nid).imagen == "a.jpg"
    for malo in ("b.exe", "sinextension", "..\\..\\etc"):  # antes: 'sinextension' causaba IndexError (HTTP 500)
        r = cn.post(f"/noticias/editar/{nid}", data=_datos((io.BytesIO(b"x"), malo)), content_type="multipart/form-data")
        assert r.status_code == 302
    assert db.session.get(Noticia, nid).imagen == "a.jpg" and sorted(p.name for p in tmp_path.iterdir()) == ["a.jpg"]
