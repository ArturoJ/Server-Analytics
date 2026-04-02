"""Endpoint de bloqueos: listado paginado con filtros y exportacion CSV."""
import csv

from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET

from ..models import Bloqueo


@require_GET
def api_bloqueos(request):
    """
    Listado paginado de bloqueos con filtros opcionales y exportacion CSV.

    Parametros GET:
        motivo: filtrar por tipo de ataque (escaneo, exceso, fuerza_bruta)
        pais: filtrar por codigo ISO de pais (ej: US, CN)
        min_pet: filtrar bloqueos con >= X peticiones
        page: numero de pagina (20 items por pagina)
        formato: 'csv' para descargar en vez de JSON (max 5000 filas)

    Respuesta JSON:
        items: lista de bloqueos con fecha, IP, pais, motivo, peticiones, regla
        total, page, total_pages: datos de paginacion
    """
    bloqueos = Bloqueo.objects.select_related('regla')

    motivo = request.GET.get('motivo')
    if motivo:
        bloqueos = bloqueos.filter(motivo=motivo)

    pais = request.GET.get('pais')
    if pais:
        bloqueos = bloqueos.filter(codigo_pais=pais)

    min_pet = request.GET.get('min_pet')
    if min_pet:
        try:
            bloqueos = bloqueos.filter(peticiones__gte=int(min_pet))
        except (ValueError, TypeError):
            pass

    formato = request.GET.get('formato')
    if formato == 'csv':
        MAX_CSV = 5000
        bloqueos_csv = bloqueos[:MAX_CSV]
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="bloqueos.csv"'
        writer = csv.writer(response)
        writer.writerow(['Fecha', 'Hora', 'IP', 'País', 'Motivo', 'Peticiones', 'Regla', 'Estado'])
        for b in bloqueos_csv:
            writer.writerow([
                b.fecha_bloqueo.strftime('%d/%m/%Y'),
                b.fecha_bloqueo.strftime('%H:%M'),
                b.ip, b.pais, b.get_motivo_display(), b.peticiones,
                b.regla.nombre if b.regla else '', 'Bloqueada' if b.activo else 'Desbloqueada',
            ])
        return response

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    per_page = 20
    total = bloqueos.count()
    items = bloqueos[(page-1)*per_page:page*per_page]

    data = []
    for b in items:
        data.append({
            'fecha': b.fecha_bloqueo.strftime('%d/%m'),
            'hora': b.fecha_bloqueo.strftime('%H:%M'),
            'ip': b.ip,
            'pais': b.pais,
            'codigo_pais': b.codigo_pais,
            'motivo': b.motivo,
            'motivo_display': b.get_motivo_display(),
            'peticiones': b.peticiones,
            'regla': b.regla.nombre if b.regla else '',
            'activo': b.activo,
        })

    return JsonResponse({
        'items': data,
        'total': total,
        'page': page,
        'total_pages': (total + per_page - 1) // per_page,
    })
