"""Pruebas de rendimiento y carga (CP-63..CP-67): RNF-03, RNF-04 y RNF-09.

* RNF-03: consultas y procesos importantes (búsqueda, solicitud de compra) con p95 <= 2.5 s.
* RNF-04: carga completa del catálogo < 4 s.
* RNF-09: 100 vehículos y 300 usuarios registrados sin degradar el rendimiento.

Método: p95 por rango más cercano (nearest-rank) sobre 30 muestras, medidas con time.perf_counter().
Alcance: se ejecutan en proceso (test client + SQLite en memoria), por lo que miden el costo de la
aplicación y no la latencia de red/Azure SQL; para eso existe scripts/medir_rendimiento.py.
Si PV_RESULTADOS apunta a un archivo, se guardan allí las mediciones (las usa el informe de calidad).
"""
import json, math, os, time
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
import bcrypt, pytest
from helpers import CsrfClient
from app import create_app, db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.seed import seed

pytestmark = pytest.mark.rendimiento
P95_MAX, CARGA_MAX, MUESTRAS = 2.5, 4.0, 30
RESULTADOS = {}


def p95(muestras):
    ordenadas = sorted(muestras)
    return ordenadas[math.ceil(0.95 * len(ordenadas)) - 1]


def medir(fn, n=MUESTRAS):
    tiempos = []
    for _ in range(n):
        t0 = time.perf_counter(); fn(); tiempos.append(time.perf_counter() - t0)
    return tiempos


def resumen(nombre, tiempos):
    RESULTADOS[nombre] = {"n": len(tiempos), "p95_s": round(p95(tiempos), 4), "max_s": round(max(tiempos), 4),
                          "media_s": round(sum(tiempos) / len(tiempos), 4)}
    print(f"\n[{nombre}] n={len(tiempos)} p95={p95(tiempos)*1000:.1f} ms max={max(tiempos)*1000:.1f} ms")


@pytest.fixture
def c():
    app = create_app(); app.config["TESTING"] = True; app.test_client_class = CsrfClient
    with app.app_context():
        db.create_all(); seed(); yield app.test_client(); db.drop_all()


@pytest.fixture(scope="module", autouse=True)
def _guardar():
    yield
    if os.getenv("PV_RESULTADOS"):
        with open(os.environ["PV_RESULTADOS"], "w", encoding="utf-8") as f: json.dump(RESULTADOS, f, indent=2)


def poblar(n_vehiculos=100, n_usuarios=300):
    """Deja la base con exactamente n_vehiculos vehículos y n_usuarios usuarios (incluye admin)."""
    motores = ["electrico", "hibrido", "combustion"]
    faltan = n_vehiculos - Vehiculo.query.count()
    db.session.add_all(Vehiculo(marca=f"Marca{i % 12}", modelo=f"Modelo {i}", anio=2018 + i % 8, precio=80_000_000 + i * 1_000_000,
                                motor=motores[i % 3], categoria=["Sedan", "SUV", "Hatchback"][i % 3],
                                emisiones_co2=0 if i % 3 == 0 else 100 + i) for i in range(faltan))
    h = bcrypt.hashpw(b"Clave1234", bcrypt.gensalt(rounds=10)).decode()  # un hash reutilizado: evita 300 x 60 ms de bcrypt
    existentes = Usuario.query.count()
    db.session.add_all(Usuario(nombre=f"u{i:03d}", email=f"u{i:03d}@x.com", telefono="3001112233", password_hash=h)
                       for i in range(n_usuarios - existentes))
    db.session.commit()


def test_cp63_rnf03_catalogo_p95(c):
    def pedir(): assert c.get("/catalogo/").status_code == 200
    t = medir(pedir); resumen("catalogo_p95", t)
    assert len(t) == 30 and p95(t) <= P95_MAX


def test_cp64_rnf03_busqueda_y_solicitud_p95(c):
    def buscar(): assert c.get("/catalogo/?motor=electrico&precio_max=400000000&categoria=SUV").status_code == 200
    t = medir(buscar); resumen("busqueda_p95", t); assert p95(t) <= P95_MAX
    c.post("/register", data={"usuario": "ana", "email": "ana@x.com", "password": "Clave1234", "telefono": "3001112233"})
    c.post("/login", data={"usuario": "ana", "password": "Clave1234"})
    poblar(40, 1 + 1)  # 40 vehículos disponibles para 30 solicitudes distintas
    ids = iter(range(1, 31))
    def solicitar(): assert c.post(f"/catalogo/{next(ids)}/solicitar").status_code == 302
    t = medir(solicitar); resumen("solicitud_compra_p95", t)
    assert p95(t) <= P95_MAX and Vehiculo.query.filter_by(estado="pendiente").count() == 30


def test_cp65_rnf04_carga_completa_catalogo(c):
    poblar(100, 2)
    def recorrer():
        pagina, vistos = 1, 0
        while True:
            r = c.get(f"/catalogo/?pagina={pagina}"); assert r.status_code == 200
            vistos += r.get_data(as_text=True).count("Ver detalle") or r.get_data(as_text=True).count("stretched-link")
            if "Siguiente" not in r.get_data(as_text=True): return pagina, vistos
            pagina += 1
    t0 = time.perf_counter(); paginas, vistos = recorrer(); total = time.perf_counter() - t0
    RESULTADOS["carga_completa_100_vehiculos_s"] = round(total, 4)
    print(f"\n[carga_completa] {paginas} páginas, {vistos} tarjetas, {total*1000:.1f} ms")
    assert paginas == 10 and vistos == 100 and total < CARGA_MAX


def test_cp66_rnf09_carga_100_vehiculos_300_usuarios(c):
    poblar(100, 300)
    assert Vehiculo.query.count() == 100 and Usuario.query.count() == 300
    t = medir(lambda: c.get("/catalogo/").status_code); resumen("catalogo_100v_300u_p95", t); assert p95(t) <= P95_MAX
    t = medir(lambda: c.get("/catalogo/?motor=hibrido&marca=Marca4").status_code); resumen("filtro_100v_p95", t); assert p95(t) <= P95_MAX
    assert c.post("/login", data={"usuario": "admin", "password": "Admin1234"}).status_code == 302
    r = c.get("/catalogo/admin/usuarios"); assert r.status_code == 200 and r.get_data(as_text=True).count("<tr>") >= 300
    t = medir(lambda: c.get("/catalogo/admin/usuarios").status_code); resumen("admin_usuarios_300_p95", t); assert p95(t) <= P95_MAX
    t = medir(lambda: c.get("/catalogo/admin/inventario").status_code); resumen("admin_inventario_100_p95", t); assert p95(t) <= P95_MAX


def test_cp67_rnf09_login_con_300_usuarios(c):
    poblar(100, 300); c.get("/logout")
    t = medir(lambda: c.post("/login", data={"usuario": "u298", "password": "Clave1234"}).status_code, n=10)
    resumen("login_bcrypt_300u_p95", t)  # bcrypt cost 10 domina el tiempo; debe seguir bajo el límite
    with c.session_transaction() as s: assert s["usuario_nombre"] == "u298"
    assert p95(t) <= P95_MAX
