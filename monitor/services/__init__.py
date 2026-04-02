"""
Servicios backend: descubrimiento de cards y geolocalizacion.
"""
from .cards import CardRegistry
from .geoip import buscar_pais, necesita_actualizar, actualizar_db
