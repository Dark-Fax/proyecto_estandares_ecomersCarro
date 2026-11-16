import os
import requests
from flask import Blueprint, render_template
from app.utils.auth import login_required

mapa = Blueprint("mapa", __name__, url_prefix="/mapa")

OCM_URL = "https://api.openchargemap.io/v3/poi/"

@mapa.route("/")
@login_required
def index():
    params = {"output": "json", "countrycode": "CO", "latitude": 4.7110, "longitude": -74.0721,
              "distance": 20, "distanceunit": "KM", "maxresults": 200}
    headers = {"X-API-Key": os.getenv("API_OCM_KEY"), "Content-Type": "application/json"}
    try:
        estaciones = requests.get(OCM_URL, params=params, headers=headers, timeout=10).json()
    except (requests.RequestException, ValueError):
        estaciones = []  # API caída o respuesta no JSON: el mapa se muestra vacío (RNF-08)
    return render_template("mapa/mapa.html", estaciones=estaciones, titulo_pagina="Mapa de Estaciones🗺️")
