"""Catálogo sostenible, compra, ventas, inventario, usuarios, dashboard y recuperación (RF-04..RF-15)."""
import io, secrets
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, request, redirect, url_for, flash,
                   session, send_file, abort)
from reportlab.pdfgen import canvas
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from app import db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo, Venta, TokenRecuperacion
from app.utils.auth import login_required, admin_required
from app.utils.correo import smtp_configurado, enviar_enlace_recuperacion

catalogo = Blueprint("catalogo", __name__, url_prefix="/catalogo", template_folder="../templates/catalogo")

def desvincular_usuario(uid):
    """Prepara el borrado de un usuario sin violar llaves foráneas (Azure SQL las exige):
    sus vehículos pendientes vuelven a 'disponible' y se eliminan sus tokens de recuperación."""
    Vehiculo.query.filter_by(solicitante_id=uid, estado="pendiente").update({"estado": "disponible"})
    Vehiculo.query.filter_by(solicitante_id=uid).update({"solicitante_id": None})
    TokenRecuperacion.query.filter_by(usuario_id=uid).delete()

# RF-04 / RF-05 / RF-06 ------------------------------------------------
# Filtros de igualdad del catálogo: parámetro de la URL -> (columna, tipo). RF-05 / HU-04.
_FILTROS_IGUALDAD = {"marca": (Vehiculo.marca, str), "categoria": (Vehiculo.categoria, str),
                     "motor": (Vehiculo.motor, str), "anio": (Vehiculo.anio, int)}

def _aplicar_filtros(q, a):
    for campo, (columna, tipo) in _FILTROS_IGUALDAD.items():
        valor = a.get(campo, type=tipo)
        if valor:
            q = q.filter(columna == valor)
    if a.get("modelo"):
        q = q.filter(Vehiculo.modelo.ilike(f"%{a['modelo']}%"))
    precio_max = a.get("precio_max", type=float)
    if precio_max:
        q = q.filter(Vehiculo.precio <= precio_max)
    return q

@catalogo.route("/")
def listado():
    a = request.args
    q = _aplicar_filtros(Vehiculo.query, a)
    pagina = a.get("pagina", 1, type=int)
    p = q.order_by(Vehiculo.motor.desc(), Vehiculo.id).paginate(page=pagina, per_page=10, error_out=False)  # HU-02: 10 por página
    marcas = [m[0] for m in db.session.query(Vehiculo.marca).distinct()]
    return render_template("catalogo/listado.html", p=p, marcas=marcas, f=a, qs={k: x for k, x in a.items() if k != 'pagina'})

@catalogo.route("/<int:vid>")
def detalle(vid):
    return render_template("catalogo/detalle.html", v=db.get_or_404(Vehiculo, vid))

# RF-07 / RF-08 --------------------------------------------------------
@catalogo.route("/<int:vid>/solicitar", methods=["POST"])
@login_required
def solicitar(vid):
    v = db.get_or_404(Vehiculo, vid)
    if v.estado != "disponible":
        flash("El vehículo ya no está disponible", "danger")
    else:
        v.estado, v.solicitante_id = "pendiente", session["usuario_id"]
        db.session.commit(); flash(f"Solicitud enviada para {v.marca} {v.modelo}", "success")
    return redirect(url_for("catalogo.detalle", vid=vid))

# RF-09 / RF-10 / RF-13 ------------------------------------------------
@catalogo.route("/admin/ventas/registrar/<int:vid>", methods=["POST"])
@admin_required
def registrar_venta(vid):
    v = db.get_or_404(Vehiculo, vid)
    if v.estado == "vendido" or Venta.query.filter_by(vehiculo_id=vid).first():
        flash("Ese vehículo ya fue vendido", "danger")
    elif not v.solicitante_id:
        flash("El vehículo no tiene un cliente solicitante", "danger")
    else:
        db.session.add(Venta(usuario_id=v.solicitante_id, vehiculo_id=vid, precio_venta=v.precio))
        v.estado = "vendido"  # equivale al trigger after_venta_insert
        db.session.commit(); flash("Venta registrada", "success")
    return redirect(url_for("catalogo.admin_inventario"))

@catalogo.route("/ventas")
@login_required
def historial():
    # joinedload: una sola consulta con JOIN en vez de 2 consultas extra por cada venta (N+1)
    q = Venta.query.options(joinedload(Venta.vehiculo), joinedload(Venta.usuario)).order_by(Venta.fecha_venta.desc())
    if session.get("rol") != "admin": q = q.filter_by(usuario_id=session["usuario_id"])
    return render_template("catalogo/ventas.html", ventas=q.all())

@catalogo.route("/ventas/<int:id>/comprobante.pdf")
@login_required
def comprobante(id):
    vt = db.get_or_404(Venta, id)
    if session.get("rol") != "admin" and vt.usuario_id != session["usuario_id"]: abort(403)
    v = vt.vehiculo
    impacto = "Vehículo de cero emisiones" if float(v.emisiones_co2) == 0 else f"Emisiones: {v.emisiones_co2} g/km CO2"
    buf = io.BytesIO(); c = canvas.Canvas(buf); y = 780
    for linea in ["PLANETA VERDE - Comprobante de venta", f"No. {vt.id}   Fecha: {vt.fecha_venta:%Y-%m-%d}",
                  f"Cliente: {vt.usuario.nombre} ({vt.usuario.email})", f"Vehiculo: {v.marca} {v.modelo} {v.anio}",
                  f"Precio de venta: ${vt.precio_venta:,.0f} COP", f"Impacto ambiental: {impacto}"]:
        c.drawString(60, y, linea); y -= 28
    c.save(); buf.seek(0)
    return send_file(buf, mimetype="application/pdf", download_name=f"comprobante_{vt.id}.pdf")

# RF-11 inventario -----------------------------------------------------
def _llenar(v, f):
    for k in ("marca", "modelo", "motor", "categoria", "imagen_url"): setattr(v, k, f.get(k, "").strip())
    v.anio, v.precio = int(f["anio"]), float(f["precio"])
    v.emisiones_co2 = float(f["emisiones_co2"])  # HU-05: obligatorio

@catalogo.route("/admin/inventario")
@admin_required
def admin_inventario():
    return render_template("catalogo/admin_inventario.html", vs=Vehiculo.query.order_by(Vehiculo.id).all())

@catalogo.route("/admin/vehiculo", methods=["GET", "POST"])
@catalogo.route("/admin/vehiculo/<int:vid>", methods=["GET", "POST"])
@admin_required
def admin_vehiculo(vid=None):
    v = db.get_or_404(Vehiculo, vid) if vid else Vehiculo(estado="disponible")
    if request.method == "POST":
        try:
            _llenar(v, request.form)
        except (KeyError, ValueError):
            flash("Complete todos los campos, incluidas las emisiones de CO2", "danger")
            return render_template("catalogo/form_vehiculo.html", v=v)
        db.session.add(v); db.session.commit(); flash("Vehículo guardado", "success")
        return redirect(url_for("catalogo.admin_inventario"))
    return render_template("catalogo/form_vehiculo.html", v=v)

@catalogo.route("/admin/vehiculo/<int:vid>/eliminar", methods=["POST"])
@admin_required
def eliminar_vehiculo(vid):
    v = db.get_or_404(Vehiculo, vid)
    if Venta.query.filter_by(vehiculo_id=vid).first():
        flash("No se puede eliminar: tiene ventas asociadas", "danger")
    else:
        db.session.delete(v); db.session.commit(); flash("Vehículo eliminado", "success")
    return redirect(url_for("catalogo.admin_inventario"))

# RF-12 usuarios -------------------------------------------------------
@catalogo.route("/admin/usuarios")
@admin_required
def admin_usuarios():
    return render_template("catalogo/admin_usuarios.html", us=Usuario.query.order_by(Usuario.id).all())

@catalogo.route("/admin/usuarios/<int:uid>/rol", methods=["POST"])
@admin_required
def cambiar_rol(uid):
    u = db.get_or_404(Usuario, uid); u.rol = "admin" if request.form.get("rol") == "admin" else "usuario"
    db.session.commit(); return redirect(url_for("catalogo.admin_usuarios"))

@catalogo.route("/admin/usuarios/<int:uid>/eliminar", methods=["POST"])
@admin_required
def eliminar_usuario(uid):
    u = db.get_or_404(Usuario, uid)
    if u.id == session["usuario_id"] or Venta.query.filter_by(usuario_id=uid).first():
        flash("No se puede eliminar este usuario", "danger")
    else:
        desvincular_usuario(uid); db.session.delete(u); db.session.commit()
    return redirect(url_for("catalogo.admin_usuarios"))

# RF-15 dashboard ------------------------------------------------------
@catalogo.route("/admin/dashboard")
@admin_required
def dashboard():
    por_motor = {"electrico": 0, "hibrido": 0, "combustion": 0}
    # RF-15: el conteo por motor lo resuelve la base de datos (1 consulta agrupada, no 1 por venta)
    for motor, n in db.session.query(Vehiculo.motor, func.count(Venta.id)).join(Venta, Venta.vehiculo_id == Vehiculo.id).group_by(Vehiculo.motor):
        por_motor[motor] = n
    total = sum(por_motor.values())
    verdes = por_motor["electrico"] + por_motor["hibrido"]
    pct = round(100 * verdes / total, 1) if total else 0
    return render_template("catalogo/dashboard.html", por_motor=por_motor, total=total, pct=pct)

# RF-14 recuperación ---------------------------------------------------
@catalogo.route("/recuperar", methods=["GET", "POST"])
def recuperar():
    if request.method == "POST":
        u = Usuario.query.filter_by(email=request.form.get("email", "").strip()).first()
        if u:
            t = TokenRecuperacion(usuario_id=u.id, token=secrets.token_urlsafe(32),
                                  fecha_expiracion=datetime.utcnow() + timedelta(minutes=15))
            db.session.add(t); db.session.commit()
            enlace = url_for("catalogo.restablecer", token=t.token, _external=True)
            if smtp_configurado():
                # Producción: el enlace solo viaja por correo; la respuesta no revela si el correo existe.
                if not enviar_enlace_recuperacion(u.email, enlace):
                    flash("No fue posible enviar el correo. Intenta de nuevo más tarde", "danger")
                    return render_template("catalogo/recuperar.html")
            else:
                # Desarrollo (sin MAIL_SERVER/MAIL_USER/MAIL_PASS): se muestra el enlace en pantalla.
                flash("Enlace (modo desarrollo, vence en 15 min): " + enlace, "info")
                return render_template("catalogo/recuperar.html")
        flash("Si el correo existe, se envió un enlace (vence en 15 minutos)", "info")
    return render_template("catalogo/recuperar.html")

@catalogo.route("/restablecer/<token>", methods=["GET", "POST"])
def restablecer(token):
    t = TokenRecuperacion.query.filter_by(token=token).first()
    if not t or t.fecha_expiracion < datetime.utcnow():
        flash("Enlace inválido o expirado", "danger"); return redirect(url_for("catalogo.recuperar"))
    if request.method == "POST":
        pw = request.form.get("password", "")
        if len(pw) < 8 or not any(c.isupper() for c in pw) or not any(c.isdigit() for c in pw):
            flash("Mínimo 8 caracteres, una mayúscula y un número", "danger")
        else:
            db.session.get(Usuario, t.usuario_id).set_password(pw)
            db.session.delete(t); db.session.commit(); flash("Contraseña actualizada", "success")
            return redirect(url_for("usuarios.login"))
    return render_template("catalogo/restablecer.html")
