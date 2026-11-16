from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models.usuario import Usuario
from app.models.vehiculo import Venta
from app.utils.auth import login_required
from app.routes.catalogo_routes import desvincular_usuario

cuenta = Blueprint("cuenta", __name__, template_folder="../templates/usuarios")

@cuenta.route("/cuenta")
@login_required
def ver_cuenta():
    usuario = db.session.get(Usuario, session["usuario_id"])
    return render_template("usuarios/cuenta.html", usuario=usuario, usuario_nombre=usuario.nombre, titulo_pagina="Configuración de Cuenta 👤")

@cuenta.route("/cuenta/editar", methods=["POST"])
@login_required
def editar_cuenta():
    usuario = db.session.get(Usuario, session["usuario_id"])
    usuario.nombre = request.form["nombre"]
    usuario.telefono = request.form["telefono"]
    usuario.email = request.form["email"]

    nueva_contrasena = request.form.get("nueva_contrasena", "").strip()
    if nueva_contrasena:
        usuario.set_password(nueva_contrasena)
        flash("Contraseña actualizada correctamente 🔒", "success")
    else:
        flash("Datos actualizados correctamente ✅", "success")

    db.session.commit()
    return redirect(url_for("cuenta.ver_cuenta"))

@cuenta.route("/cuenta/eliminar", methods=["POST"])
@login_required
def eliminar_cuenta():
    usuario = db.session.get(Usuario, session["usuario_id"])
    if Venta.query.filter_by(usuario_id=usuario.id).first():
        flash("No puedes eliminar la cuenta: tienes compras registradas", "danger")
        return redirect(url_for("cuenta.ver_cuenta"))
    desvincular_usuario(usuario.id)  # solicitudes pendientes y tokens
    db.session.delete(usuario)
    db.session.commit()
    session.clear()

    flash("Tu cuenta ha sido eliminada permanentemente", "info")
    return redirect(url_for("usuarios.registro"))