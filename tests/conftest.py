import pytest


@pytest.fixture(autouse=True)
def _sin_smtp(monkeypatch):
    """Por defecto no hay SMTP: la recuperación usa el modo desarrollo (enlace en pantalla)."""
    for v in ("MAIL_SERVER", "MAIL_USER", "MAIL_PASS", "MAIL_PORT", "MAIL_FROM"):
        monkeypatch.delenv(v, raising=False)
