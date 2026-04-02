"""Vista de estadisticas por pais."""
from django.shortcuts import render


def estadisticas_paises(request):
    """Estadisticas por pais. Datos via fetch a /api/estadisticas/paises/."""
    return render(request, 'estadisticas/paises.html')
