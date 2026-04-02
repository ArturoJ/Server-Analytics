"""Endpoint de reglas de deteccion con estadisticas del dia."""
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..models import Bloqueo, ReglaDeteccion


@require_GET
def api_reglas(request):
    """
    Reglas de deteccion con estadisticas del dia actual.

    Respuesta JSON:
        reglas: lista con nombre, tipo, estado, disparos/IPs/peticiones del dia
    """
    reglas = ReglaDeteccion.objects.all()
    hoy = timezone.now().date()
    data = []
    for r in reglas:
        bloqueos_regla = Bloqueo.objects.filter(regla=r, fecha_bloqueo__date=hoy)
        data.append({
            'nombre': r.nombre,
            'tipo': r.tipo,
            'tipo_display': r.get_tipo_display(),
            'activa': r.activa,
            'descripcion': r.descripcion,
            'disparos_hoy': bloqueos_regla.count(),
            'ips_hoy': bloqueos_regla.values('ip').distinct().count(),
            'peticiones_hoy': bloqueos_regla.aggregate(t=Sum('peticiones'))['t'] or 0,
        })
    return JsonResponse({'reglas': data})
