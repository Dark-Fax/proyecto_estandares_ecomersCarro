#!/usr/bin/env python3
"""Mide RNF-03 y RNF-04 contra un despliegue real (Azure) por HTTP.

Uso:  python scripts/medir_rendimiento.py https://mi-app.azurewebsites.net [--muestras 30]
Imprime p95 de GET /catalogo/ y el tiempo de carga completa (todas las páginas).
Código de salida 0 si cumple (p95 <= 2.5 s y carga completa < 4 s), 1 si no cumple.
"""
import argparse, math, sys, time
import requests

P95_MAX, CARGA_MAX = 2.5, 4.0


def p95(m):
    s = sorted(m); return s[math.ceil(0.95 * len(s)) - 1]


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("base_url"); ap.add_argument("--muestras", type=int, default=30)
    a = ap.parse_args(); base = a.base_url.rstrip("/"); s = requests.Session()
    tiempos = []
    for _ in range(a.muestras):
        t0 = time.perf_counter(); r = s.get(f"{base}/catalogo/", timeout=30); tiempos.append(time.perf_counter() - t0)
        r.raise_for_status()
    t0 = time.perf_counter(); pagina = 1
    while True:
        html = s.get(f"{base}/catalogo/?pagina={pagina}", timeout=30).text
        if "Siguiente" not in html: break
        pagina += 1
    carga = time.perf_counter() - t0
    ok3, ok4 = p95(tiempos) <= P95_MAX, carga < CARGA_MAX
    print(f"RNF-03  GET /catalogo/  n={len(tiempos)}  p95={p95(tiempos):.3f} s  (límite {P95_MAX} s)  {'CUMPLE' if ok3 else 'NO CUMPLE'}")
    print(f"RNF-04  carga completa ({pagina} páginas)  {carga:.3f} s  (límite {CARGA_MAX} s)  {'CUMPLE' if ok4 else 'NO CUMPLE'}")
    sys.exit(0 if ok3 and ok4 else 1)


if __name__ == "__main__":
    main()
