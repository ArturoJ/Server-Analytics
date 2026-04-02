"""Endpoint principal del dashboard: KPIs, graficos y ultimos bloqueos."""
from django.db.models import Sum, Count
from django.db.models.functions import ExtractHour
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from ..models import Bloqueo, Visita


def codigo_a_bandera(code):
    """Convierte un codigo ISO de pais (ej: 'ES') en su emoji de bandera."""
    if not code or len(code) != 2:
        return ''
    return chr(0x1F1E6 + ord(code[0].upper()) - ord('A')) + chr(0x1F1E6 + ord(code[1].upper()) - ord('A'))


@require_GET
def api_dashboard(request):
    """
    Endpoint principal del dashboard.

    Parametros GET opcionales:
        desde: fecha ISO para filtrar bloqueos (sin este parametro devuelve todo el acumulado)

    Respuesta JSON:
        kpis: IPs bloqueadas, peticiones, paises, IP mas agresiva, visitantes
        por_hora: distribucion de bloqueos por hora del dia
        por_tipo: distribucion por tipo de ataque (escaneo, exceso, fuerza_bruta)
        top_ips: las 5 IPs con mas peticiones bloqueadas
        ultimos: los 15 bloqueos mas recientes
    """
    desde_param = request.GET.get('desde')
    if desde_param:
        try:
            desde = timezone.datetime.fromisoformat(desde_param)
            if timezone.is_naive(desde):
                desde = timezone.make_aware(desde)
        except ValueError:
            desde = None
    else:
        desde = None

    bloqueos = Bloqueo.objects.filter(fecha_bloqueo__gte=desde) if desde else Bloqueo.objects.all()

    total_ips = bloqueos.values('ip').distinct().count()
    total_pet = bloqueos.aggregate(t=Sum('peticiones'))['t'] or 0
    paises = [p for p in set(bloqueos.values_list('codigo_pais', flat=True)) if p]
    banderas_list = [codigo_a_bandera(p) for p in paises]

    ip_top = bloqueos.values('ip', 'pais', 'codigo_pais').annotate(
        total=Sum('peticiones')
    ).order_by('-total').first()

    por_hora_raw = bloqueos.annotate(
        hora_num=ExtractHour('fecha_bloqueo')
    ).values('hora_num').annotate(total=Count('id')).order_by('hora_num')
    por_hora = [{'hora': str(h['hora_num']).zfill(2), 'total': h['total']} for h in por_hora_raw]

    por_tipo = list(bloqueos.values('motivo').annotate(total=Count('id')))

    top_ips = list(bloqueos.values('ip').annotate(
        total=Sum('peticiones')
    ).order_by('-total')[:5])

    ultimos_qs = bloqueos.select_related('regla')[:15]
    ultimos = []
    for b in ultimos_qs:
        ultimos.append({
            'ip': b.ip,
            'pais': b.pais,
            'codigo_pais': b.codigo_pais,
            'motivo': b.motivo,
            'peticiones': b.peticiones,
            'fecha_bloqueo': b.fecha_bloqueo.isoformat(),
            'activo': b.activo,
            'regla': b.regla.nombre if b.regla else '',
        })

    total_visitantes = Visita.objects.count()
    total_visitas_pet = Visita.objects.aggregate(t=Sum('peticiones'))['t'] or 0

    return JsonResponse({
        'kpis': {
            'total_ips': total_ips,
            'total_peticiones': total_pet,
            'paises': len(paises),
            'banderas_list': banderas_list,
            'ip_top': ip_top,
            'visitantes': total_visitantes,
            'visitas_peticiones': total_visitas_pet,
        },
        'por_hora': por_hora,
        'por_tipo': por_tipo,
        'top_ips': top_ips,
        'ultimos': ultimos,
        'ultimo_ts': timezone.now().isoformat(),
    })
