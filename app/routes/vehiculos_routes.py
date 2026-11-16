from flask import Blueprint, render_template, session, redirect, url_for
from app.utils.auth import login_required

vehiculos = Blueprint('vehiculos', __name__, url_prefix='/vehiculos')

@vehiculos.route('/listar')
@login_required
def listar():
    return render_template('vehiculos/listar.html', usuario_nombre=session['usuario_nombre'],
                           titulo_pagina="Catálogo de vehículos eléctricos ⚡")

# Las seis fichas estáticas (Kia, BMW, Bolt, Leaf, Volvo, Tesla) estaban duplicadas con el catálogo
# dinámico de la base de datos. Se conservan las URL antiguas como redirecciones (HTTP 302)
# al catálogo filtrado por marca, para no romper enlaces ni marcadores existentes.
_MARCA_POR_RUTA = {'kia': 'Kia', 'bmw': 'BMW', 'bolt': 'Chevrolet',
                   'leaf': 'Nissan', 'volvo': 'Volvo', 'tesla': 'Tesla'}

def _al_catalogo(ruta):
    def vista():
        return redirect(url_for('catalogo.listado', marca=_MARCA_POR_RUTA[ruta]))
    vista.__name__ = ruta  # conserva los endpoints vehiculos.kia, vehiculos.bmw, ...
    return vista

for _ruta in _MARCA_POR_RUTA:
    vehiculos.add_url_rule(f'/{_ruta}', endpoint=_ruta, view_func=_al_catalogo(_ruta))
