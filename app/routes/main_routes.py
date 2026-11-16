from flask import Blueprint, session, redirect, url_for
from app.utils.auth import login_required

main = Blueprint('main', __name__)

@main.route('/')
def home():
    # Con sesión se va al panel de noticias; sin sesión, al login.
    if 'usuario_id' in session:
        return redirect(url_for('noticias.inicio_noticias'))
    return redirect(url_for('usuarios.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    # El dashboard ambiental (RF-15) vive en el catálogo y es solo para administradores.
    if session.get('rol') == 'admin':
        return redirect(url_for('catalogo.dashboard'))
    return redirect(url_for('noticias.inicio_noticias'))
