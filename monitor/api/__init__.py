"""
API endpoints de Server Analytics (solo lectura, JSON).

Cada archivo corresponde a un endpoint.
"""
from .dashboard import api_dashboard
from .bloqueos import api_bloqueos
from .estadisticas import api_estadisticas_paises
from .reglas import api_reglas
