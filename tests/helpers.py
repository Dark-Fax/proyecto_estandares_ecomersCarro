"""Cliente de pruebas con CSRF activo: extrae el token del formulario real y lo envía en cada POST.

La protección CSRF NO se desactiva en las pruebas (WTF_CSRF_ENABLED queda en True), de modo que
las 40 pruebas originales verifican el sistema con la defensa encendida. Para probar el rechazo
sin token se pone ``client.auto_csrf = False``.
"""
import re
from flask import g
from flask.testing import FlaskClient

_TOKEN = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


class CsrfClient(FlaskClient):
    auto_csrf = True

    def token(self):
        # Las fixtures mantienen un app_context abierto: Flask-WTF cachea el token en ``g`` y,
        # tras un logout, no volvería a escribirlo en la sesión. En producción cada petición
        # tiene su propio contexto, por eso esto solo es necesario en las pruebas.
        g.pop("csrf_token", None)
        html = super().open("/login", method="GET").get_data(as_text=True)
        return _TOKEN.search(html).group(1)

    def open(self, *args, **kwargs):
        if self.auto_csrf and (kwargs.get("method") or "GET").upper() == "POST":
            data = kwargs.get("data")
            if data is None or isinstance(data, dict):
                data = dict(data or {})
                data.setdefault("csrf_token", self.token())
                kwargs["data"] = data
        return super().open(*args, **kwargs)
