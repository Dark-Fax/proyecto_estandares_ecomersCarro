"""Decoradores de autorización compartidos por todos los blueprints (HU-05, HU-09).

Antes había dos copias distintas (catálogo y noticias) y otros módulos repetían
``if "usuario_nombre" not in session`` en cada ruta. Ahora hay una sola fuente de verdad.
La sesión se considera iniciada cuando existe ``usuario_id`` (lo fija usuarios.login).
"""
from functools import wraps
from flask import flash, redirect, session, url_for


def login_required(f):
    """Exige sesión activa; si no, redirige al login con un aviso."""
    @wraps(f)
    def envoltura(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Debes iniciar sesión", "danger")
            return redirect(url_for("usuarios.login"))
        return f(*args, **kwargs)
    return envoltura


def admin_required(f=None, *, destino="catalogo.listado"):
    """Exige sesión activa con rol ``admin``.

    Se usa como ``@admin_required`` o ``@admin_required(destino="noticias.listar")``
    cuando el usuario sin permisos debe volver a otra pantalla.
    """
    def decorador(fn):
        @wraps(fn)
        @login_required
        def envoltura(*args, **kwargs):
            if session.get("rol") != "admin":
                flash("Solo administradores", "danger")
                return redirect(url_for(destino))
            return fn(*args, **kwargs)
        return envoltura
    return decorador(f) if f is not None else decorador
