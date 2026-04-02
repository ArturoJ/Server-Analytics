"""Context processors para inyectar variables de configuracion en los templates."""
from django.conf import settings


def site_config(request):
    """Inyecta SITE_DOMAIN y SITE_AUTHOR en todos los templates."""
    return {
        'SITE_DOMAIN': settings.SITE_DOMAIN,
        'SITE_AUTHOR': getattr(settings, 'SITE_AUTHOR', ''),
        'SITE_AUTHOR_URL': getattr(settings, 'SITE_AUTHOR_URL', ''),
    }
