"""Paginas auxiliares: SEO (robots, sitemap), PWA (service worker) y honeypot."""
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


def service_worker(request):
    """Sirve el service worker desde /sw.js (debe estar en la raiz para el scope de la PWA)."""
    from django.contrib.staticfiles.finders import find as find_static
    sw_path = find_static('sw.js')
    if not sw_path:
        sw_path = settings.BASE_DIR / 'static' / 'sw.js'
    with open(sw_path) as f:
        content = f.read()
    return HttpResponse(content, content_type='application/javascript')


def robots_txt(request):
    """Directivas para crawlers. Permite indexar todo el sitio."""
    domain = settings.SITE_DOMAIN
    content = (
        "User-agent: *\n"
        "Allow: /\n"
        f"Sitemap: {domain}/sitemap.xml\n"
    )
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    """Mapa del sitio XML para SEO."""
    domain = settings.SITE_DOMAIN
    urls = [
        '/', '/bloqueos/', '/estadisticas/paises/',
        '/servidores/', '/reglas/', '/contacto/',
    ]
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for url in urls:
        xml += f'  <url><loc>{domain}{url}</loc></url>\n'
    xml += '</urlset>'
    return HttpResponse(xml, content_type='application/xml')


@csrf_exempt
def contacto(request):
    """
    Honeypot: formulario de contacto falso para atraer bots.

    El POST no guarda ni envia nada, solo devuelve un JSON de exito
    para que el bot crea que funciono. csrf_exempt para que los bots
    puedan enviar sin token CSRF.
    """
    if request.method == 'POST':
        return JsonResponse({'status': 'ok', 'message': 'Mensaje enviado'})
    return render(request, 'contacto.html')


def csrf_failure(request, reason=''):
    """Pagina custom de error CSRF para no revelar el framework."""
    return HttpResponse('<h1>403 Prohibido</h1>', status=403, content_type='text/html')
