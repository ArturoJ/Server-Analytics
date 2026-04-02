"""Vista de la lista de servidores monitorizados."""
from django.shortcuts import render
from django.utils import timezone

from ..models import Servidor


def servidores_lista(request):
    """Lista de servidores monitorizados con bloqueos del dia y ultima actividad."""
    servidores = Servidor.objects.all()
    for s in servidores:
        s.bloqueos_hoy = s.bloqueos.filter(
            fecha_bloqueo__date=timezone.now().date()
        ).count()
        ultimo = s.bloqueos.first()
        s.ultima_actividad = ultimo.fecha_bloqueo if ultimo else None
    return render(request, 'servidores/lista.html', {'servidores': servidores})
