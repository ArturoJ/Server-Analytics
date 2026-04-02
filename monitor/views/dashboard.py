"""Vista del dashboard modular con cards personalizables."""
import json

from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie

from ..models import Dashboard, CardModule
from ..services import CardRegistry


@ensure_csrf_cookie
def dashboard(request):
    """
    Pagina principal: dashboard modular con cards personalizables.

    Carga el dashboard por defecto (pk=1), lee los modulos de cards
    desde disco via CardRegistry, e inyecta sus templates/CSS/JS
    en el HTML para que el frontend los renderice.

    El layout se guarda en localStorage del navegador, no en el servidor.
    """
    dash, _ = Dashboard.objects.get_or_create(pk=1, defaults={'nombre': 'Principal'})
    cards = dash.cards.select_related('module').all()
    modules = CardModule.objects.filter(activo=True)

    card_slugs = set(c.module.slug for c in cards)
    card_slugs.update(m.slug for m in modules)

    card_styles = {}
    card_scripts = {}
    card_templates = {}
    for slug in card_slugs:
        style = CardRegistry.get_style(slug)
        if style:
            card_styles[slug] = style.read_text()
        script = CardRegistry.get_script(slug)
        if script:
            card_scripts[slug] = script.read_text()
        tpl = CardRegistry.get_template(slug)
        if tpl:
            card_templates[slug] = tpl.read_text()

    cards_json = []
    for c in cards:
        cards_json.append({
            'id': c.pk,
            'instance_id': str(c.instance_id),
            'module_slug': c.module.slug,
            'module_nombre': c.module.nombre,
            'module_color': c.module.color,
            'label': c.label,
            'config': c.config,
            'grid_x': c.grid_x, 'grid_y': c.grid_y,
            'grid_w': c.grid_w, 'grid_h': c.grid_h,
            'z_index': c.z_index,
        })

    modules_json = []
    for m in modules:
        modules_json.append({
            'slug': m.slug, 'nombre': m.nombre,
            'descripcion': m.descripcion, 'color': m.color,
            'default_w': m.default_w, 'default_h': m.default_h,
            'categoria': m.categoria,
        })

    return render(request, 'dashboard.html', {
        'dashboard': dash,
        'dashboard_id': dash.pk,
        'cards_json': json.dumps(cards_json),
        'modules_json': json.dumps(modules_json),
        'card_styles': card_styles,
        'card_scripts': card_scripts,
        'card_templates': card_templates,
    })
