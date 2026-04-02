"""Endpoint de estadisticas de bloqueos agrupadas por pais."""
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from ..models import Bloqueo
from .dashboard import codigo_a_bandera


@require_GET
def api_estadisticas_paises(request):
    """
    Estadisticas de bloqueos agrupadas por pais.

    Respuesta JSON:
        ranking: lista de paises ordenados por peticiones (pais, bandera, IPs, peticiones, IP top, %)
        total_paises, total_peticiones, total_ips: contadores globales
        franjas: franjas horarias de 4 horas
        por_franja: actividad de cada pais por franja horaria (para grafico stacked)
    """
    bloqueos = Bloqueo.objects.all()

    paises_data = {}
    for b in bloqueos.select_related('regla'):
        c = b.codigo_pais or '_desconocido'
        nombre = b.pais or 'Desconocido'
        if c not in paises_data:
            paises_data[c] = {'pais': nombre, 'codigo': c if c != '_desconocido' else '', 'ips': set(), 'pet': 0, 'ip_top': None, 'ip_top_pet': 0, 'ultimo': None}
        paises_data[c]['ips'].add(b.ip)
        paises_data[c]['pet'] += b.peticiones
        if b.peticiones > paises_data[c]['ip_top_pet']:
            paises_data[c]['ip_top'] = b.ip
            paises_data[c]['ip_top_pet'] = b.peticiones
        if paises_data[c]['ultimo'] is None or b.fecha_bloqueo > paises_data[c]['ultimo']:
            paises_data[c]['ultimo'] = b.fecha_bloqueo

    total_pet = sum(p['pet'] for p in paises_data.values())
    total_ips = len(set(b.ip for b in bloqueos))

    ranking = sorted(paises_data.values(), key=lambda p: p['pet'], reverse=True)
    result = []
    for p in ranking:
        result.append({
            'pais': p['pais'],
            'codigo': p['codigo'],
            'bandera': codigo_a_bandera(p['codigo']),
            'ips': len(p['ips']),
            'peticiones': p['pet'],
            'ip_top': p['ip_top'],
            'ip_top_pet': p['ip_top_pet'],
            'ultimo': p['ultimo'].strftime('%d/%m %H:%M') if p['ultimo'] else '',
            'porcentaje': round(p['pet'] / total_pet * 100, 1) if total_pet else 0,
        })

    franjas = ['00-04', '04-08', '08-12', '12-16', '16-20', '20-24']
    por_franja = {}
    for p in paises_data:
        por_franja[p] = [0] * 6
    for b in bloqueos:
        hora = b.fecha_bloqueo.hour
        idx = hora // 4
        if b.codigo_pais in por_franja:
            por_franja[b.codigo_pais][idx] += 1

    franja_series = []
    for p in ranking:
        franja_series.append({
            'pais': p['pais'],
            'codigo': p['codigo'],
            'datos': por_franja.get(p['codigo'], [0]*6),
        })

    return JsonResponse({
        'ranking': result,
        'total_paises': len(ranking),
        'total_peticiones': total_pet,
        'total_ips': total_ips,
        'franjas': franjas,
        'por_franja': franja_series,
    })
