"""Vista de reglas de deteccion con estadisticas del dia."""
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone

from ..models import Bloqueo, ReglaDeteccion


def reglas_lista(request):
    """
    Lista de reglas de deteccion con estadisticas del dia.

    Calcula para cada regla: disparos, IPs bloqueadas y peticiones del dia.
    Identifica la regla mas activa para destacarla en la cabecera.
    """
    reglas = ReglaDeteccion.objects.all()
    hoy = timezone.now().date()
    total_disparos = 0
    total_ips_bloqueadas = 0
    regla_top = None
    regla_top_disparos = 0

    for r in reglas:
        bloqueos_regla = Bloqueo.objects.filter(regla=r, fecha_bloqueo__date=hoy)
        r.disparos_hoy = bloqueos_regla.count()
        r.ips_hoy = bloqueos_regla.values('ip').distinct().count()
        r.peticiones_hoy = bloqueos_regla.aggregate(t=Sum('peticiones'))['t'] or 0
        ultimo = bloqueos_regla.first()
        r.ultimo_disparo = ultimo.fecha_bloqueo if ultimo else None
        total_disparos += r.disparos_hoy
        total_ips_bloqueadas += r.ips_hoy
        if r.disparos_hoy > regla_top_disparos:
            regla_top = r
            regla_top_disparos = r.disparos_hoy

    activas = sum(1 for r in reglas if r.activa)
    inactivas = len(reglas) - activas

    return render(request, 'reglas/lista.html', {
        'reglas': reglas,
        'total_reglas': len(reglas),
        'activas': activas,
        'inactivas': inactivas,
        'total_disparos': total_disparos,
        'total_ips_bloqueadas': total_ips_bloqueadas,
        'regla_top': regla_top,
        'regla_top_disparos': regla_top_disparos,
    })
