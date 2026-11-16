from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from app import db
from app.models.noticia import Noticia
from app.utils.auth import login_required, admin_required
from werkzeug.utils import secure_filename
import os




noticias = Blueprint(
    "noticias",
    __name__,
    url_prefix="/noticias",
)

def _guardar_imagen(archivo):
    """Valida la extensión y guarda la imagen subida. Devuelve el nombre guardado o None."""
    if not archivo or archivo.filename == "":
        return None
    nombre = secure_filename(archivo.filename)
    extension = nombre.rsplit(".", 1)[1].lower() if "." in nombre else ""
    if extension not in current_app.config["ALLOWED_EXTENSIONS"]:
        flash("Formato de imagen no permitido", "danger")
        return None
    archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre))
    return nombre


# -------------------------------
# RUTAS CRUD NOTICIAS
# -------------------------------


# Listar noticias (todos los usuarios)


@noticias.route("/inicio")
@login_required
def inicio_noticias():
    return render_template(
        "noticias/panel.html",  # <--- Nuevo nombre que coincide con el archivo
        usuario_nombre=session["usuario_nombre"],
        titulo_pagina="Inicio Noticias"
    )

@noticias.route("/listar")
@login_required
def listar():
    noticias_all = Noticia.query.all()
    return render_template(
        "noticias/listar_Noticias.html",
        noticias=noticias_all,
        usuario_nombre=session["usuario_nombre"],
        titulo_pagina="Listado de Noticias 📰",
    )


# Formulario real de creación de noticia (solo admin)
@noticias.route("/crear_formulario", methods=["GET", "POST"])
@admin_required(destino="noticias.listar")
def crear_formulario():
    if request.method == "POST":
        titulo = request.form["titulo"]
        categoria = request.form["categoria"]
        autor = session.get("usuario_nombre")
        contenido = request.form["contenido"]
        vistas = int(request.form.get("vistas", 0))
        filename = _guardar_imagen(request.files.get('imagen'))

        nueva_noticia = Noticia(
            titulo=titulo,
            categoria=categoria,
            autor=autor,
            contenido=contenido,
            vistas=vistas,
            imagen=filename,
        )
        db.session.add(nueva_noticia)
        db.session.commit()
        flash("Noticia creada correctamente", "success")
        return redirect(url_for("noticias.listar"))

    return render_template(
        "noticias/crear_noticias_formulario.html",
        usuario_nombre=session["usuario_nombre"],
        titulo_pagina="Crear Noticia ✏️",
    )


# Ver noticia individual (todos los usuarios)
@noticias.route("/ver/<int:id>")
@login_required
def ver(id):
    noticia = Noticia.query.get_or_404(id)
    return render_template(
        "noticias/ver_noticia.html",
        noticia=noticia,
        usuario_nombre=session["usuario_nombre"],
        titulo_pagina=noticia.titulo,
    )


# Editar noticia (solo admin)
@noticias.route("/editar/<int:id>", methods=["GET", "POST"])
@admin_required(destino="noticias.listar")
def editar(id):
    noticia = Noticia.query.get_or_404(id)

    if request.method == "POST":
        # Actualizar campos de texto
        noticia.titulo = request.form["titulo"]
        noticia.categoria = request.form["categoria"]
        noticia.contenido = request.form["contenido"]
        noticia.vistas = int(request.form.get("vistas", noticia.vistas))

        nueva_imagen = _guardar_imagen(request.files.get('imagen'))
        if nueva_imagen:
            noticia.imagen = nueva_imagen

        # Guardar cambios en la base de datos
        db.session.commit()
        flash("Noticia actualizada correctamente", "success")
        return redirect(url_for("noticias.listar"))

    return render_template(
        "noticias/editar_Noticias.html",
        noticia=noticia,
        usuario_nombre=session["usuario_nombre"],
        titulo_pagina="Editar Noticia ✏️",
    )


# Eliminar noticia (solo admin)
@noticias.route("/eliminar/<int:id>", methods=["POST"])
@admin_required(destino="noticias.listar")
def eliminar(id):
    # Evitar que se borren las noticias de prueba
    if id in [1, 2]:
        flash("No se puede eliminar esta noticia de prueba", "info")
        return redirect(url_for("noticias.listar"))

    noticia = Noticia.query.get_or_404(id)
    db.session.delete(noticia)
    db.session.commit()
    flash("Noticia eliminada correctamente", "success")
    return redirect(url_for("noticias.listar"))
