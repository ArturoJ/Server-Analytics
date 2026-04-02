"""Sincroniza los modulos de cards desde disco y crea el dashboard por defecto."""
from django.core.management.base import BaseCommand
from monitor.models import Dashboard, CardModule, CardInstance
from monitor.services import CardRegistry


DEFAULT_CARDS = [
    {'slug': 'kpi', 'config': {'tipo': 'ips'}, 'x': 0, 'y': 0, 'w': 15, 'h': 7},
    {'slug': 'kpi', 'config': {'tipo': 'peticiones'}, 'x': 15, 'y': 0, 'w': 15, 'h': 7},
    {'slug': 'kpi', 'config': {'tipo': 'ip_top'}, 'x': 30, 'y': 0, 'w': 15, 'h': 7},
    {'slug': 'kpi', 'config': {'tipo': 'paises'}, 'x': 45, 'y': 0, 'w': 15, 'h': 7},
    {'slug': 'kpi', 'config': {'tipo': 'visitantes'}, 'x': 60, 'y': 0, 'w': 15, 'h': 7},
    {'slug': 'grafico_hora', 'config': {}, 'x': 0, 'y': 7, 'w': 20, 'h': 14},
    {'slug': 'grafico_tipo', 'config': {}, 'x': 20, 'y': 7, 'w': 20, 'h': 14},
    {'slug': 'top_ips', 'config': {}, 'x': 40, 'y': 7, 'w': 20, 'h': 14},
    {'slug': 'paises', 'config': {}, 'x': 0, 'y': 21, 'w': 30, 'h': 16},
    {'slug': 'reglas', 'config': {}, 'x': 30, 'y': 21, 'w': 30, 'h': 14},
    {'slug': 'tabla_bloqueos', 'config': {}, 'x': 0, 'y': 37, 'w': 60, 'h': 18},
]


class Command(BaseCommand):
    help = 'Sincroniza los modulos de cards desde disco y crea el dashboard por defecto'

    def handle(self, *args, **options):
        CardRegistry.sync_to_db()
        modules = CardModule.objects.filter(activo=True)
        self.stdout.write(f'{modules.count()} modulos sincronizados')

        dash, created = Dashboard.objects.get_or_create(pk=1, defaults={'nombre': 'Principal'})
        if created or not dash.cards.exists():
            dash.cards.all().delete()
            for item in DEFAULT_CARDS:
                module = CardModule.objects.filter(slug=item['slug']).first()
                if module:
                    CardInstance.objects.create(
                        dashboard=dash,
                        module=module,
                        config=item.get('config', {}),
                        grid_x=item['x'],
                        grid_y=item['y'],
                        grid_w=item['w'],
                        grid_h=item['h'],
                    )
            self.stdout.write(self.style.SUCCESS(f'Dashboard creado con {len(DEFAULT_CARDS)} cards'))
        else:
            self.stdout.write(f'Dashboard existente con {dash.cards.count()} cards')
