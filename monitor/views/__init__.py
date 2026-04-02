"""
Vistas de paginas HTML, organizadas por seccion.

Cada archivo corresponde a una seccion del sitio.
Este __init__.py re-exporta todo para que urls.py siga funcionando
con 'from . import views' sin cambiar nada.
"""
from .dashboard import dashboard
from .bloqueos import bloqueos_lista, detalle_ip
from .estadisticas import estadisticas_paises
from .servidores import servidores_lista
from .reglas import reglas_lista
from .seo import service_worker, robots_txt, sitemap_xml, contacto, csrf_failure
