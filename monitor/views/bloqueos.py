"""Vistas de bloqueos: lista y detalle de IP."""
import re

from django.shortcuts import render

from ..models import Bloqueo


def bloqueos_lista(request):
    """Lista de bloqueos. Los datos se cargan via fetch a /api/bloqueos/."""
    return render(request, 'bloqueos/lista.html')


def detalle_ip(request, ip):
    """
    Detalle de una IP bloqueada: timeline de bloqueos y rutas solicitadas.

    Valida el formato de la IP con regex antes de consultar la BD
    para evitar inyecciones en la query.
    """
    if not re.match(r'^[\d.:a-fA-F]+$', ip):
        return render(request, 'bloqueos/detalle_ip.html', {'ip': ip, 'bloqueos': Bloqueo.objects.none()})
    bloqueos = Bloqueo.objects.filter(ip=ip).select_related('servidor', 'regla')
    return render(request, 'bloqueos/detalle_ip.html', {'ip': ip, 'bloqueos': bloqueos})
