"""
Geolocalizacion de IPs con base de datos local.

Usa la BD gratuita de DB-IP (formato MMDB, compatible con geoip2).
Se descarga por HTTPS y se almacena en data/geoip-country.mmdb.
Se auto-actualiza cada 24 horas desde el daemon analizar_logs.

Ventajas sobre APIs externas:
- Sin trafico de red en cada consulta (consulta local instantanea)
- Sin limites de peticiones
- Sin riesgo de MITM (descarga por HTTPS, consulta local)
"""
import gzip
import shutil
import time
import urllib.error
import urllib.request
import geoip2.errors
from datetime import datetime
from pathlib import Path

from django.conf import settings

GEOIP_DIR = Path(settings.BASE_DIR) / 'data'
GEOIP_DB = GEOIP_DIR / 'geoip-country.mmdb'
MAX_EDAD_SEGUNDOS = 86400

_reader = None


def _download_url():
    """Genera la URL de descarga de DB-IP para el mes actual."""
    now = datetime.now()
    return f'https://download.db-ip.com/free/dbip-country-lite-{now.year}-{now.month:02d}.mmdb.gz'


def necesita_actualizar():
    """Devuelve True si la BD no existe o tiene mas de 24 horas."""
    if not GEOIP_DB.exists():
        return True
    edad = time.time() - GEOIP_DB.stat().st_mtime
    return edad >= MAX_EDAD_SEGUNDOS


def actualizar_db():
    """
    Descarga la BD GeoIP desde DB-IP y la descomprime.

    Proceso: descarga .mmdb.gz -> descomprime a .mmdb -> borra el .gz.
    Resetea el reader para que la proxima consulta use la BD nueva.
    """
    GEOIP_DIR.mkdir(exist_ok=True)
    gz_path = GEOIP_DIR / 'geoip-country.mmdb.gz'
    req = urllib.request.Request(_download_url(), headers={'User-Agent': 'ServerAnalytics/1.0'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        with open(gz_path, 'wb') as f:
            shutil.copyfileobj(resp, f)
    with gzip.open(gz_path, 'rb') as f_in:
        with open(GEOIP_DB, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    gz_path.unlink()
    global _reader
    _reader = None


def _get_reader():
    """Devuelve el reader de geoip2. Lo crea una sola vez y lo reutiliza (singleton)."""
    global _reader
    if _reader is None:
        import geoip2.database
        _reader = geoip2.database.Reader(str(GEOIP_DB))
    return _reader


def buscar_pais(ip):
    """
    Busca el pais de una IP en la BD local.

    Returns:
        tuple: (nombre_pais, codigo_iso) ej: ('Francia', 'FR')
               Devuelve ('', '') si la IP no se encuentra o hay error.
    """
    try:
        reader = _get_reader()
        resp = reader.country(ip)
        nombre = resp.country.names.get('es', resp.country.name) or ''
        codigo = resp.country.iso_code or ''
        return (nombre, codigo)
    except (geoip2.errors.AddressNotFoundError, ValueError):
        return ('', '')
    except FileNotFoundError:
        import logging
        logging.getLogger(__name__).warning('BD GeoIP no encontrada. Ejecuta el daemon para descargarla.')
        return ('', '')
