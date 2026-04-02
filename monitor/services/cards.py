"""
CardRegistry: descubrimiento automatico de modulos de cards desde disco.

Cada card es una carpeta dentro de CARDS_DIR (settings.py) con 4 archivos:
    card.json      -> metadatos (slug, nombre, descripcion, color, tamano)
    template.html  -> HTML del contenido de la card
    style.css      -> estilos especificos de la card
    script.js      -> logica JS (init, update, destroy, resize)

El metodo sync_to_db() sincroniza las carpetas con la tabla CardModule.
Si se borra una carpeta, el modulo se desactiva en la BD.
"""
import json
from pathlib import Path
from django.conf import settings


class CardRegistry:

    @classmethod
    def discover(cls):
        """Escanea CARDS_DIR y devuelve la lista de metadatos de cada card encontrada."""
        found = []
        cards_dir = Path(settings.CARDS_DIR)
        if not cards_dir.exists():
            return found
        for child in sorted(cards_dir.iterdir()):
            meta_file = child / 'card.json'
            if child.is_dir() and meta_file.exists():
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                meta['_dir'] = str(child)
                found.append(meta)
        return found

    @classmethod
    def sync_to_db(cls):
        """
        Sincroniza las cards del disco con la tabla CardModule.

        Crea o actualiza los modulos que existen en disco.
        Desactiva los que ya no tienen carpeta.
        """
        from monitor.models import CardModule
        discovered = cls.discover()
        slugs = set()
        for meta in discovered:
            slug = meta['slug']
            slugs.add(slug)
            defaults = meta.get('default_size', {})
            CardModule.objects.update_or_create(
                slug=slug,
                defaults={
                    'nombre': meta.get('nombre', slug),
                    'descripcion': meta.get('descripcion', ''),
                    'color': meta.get('color', '#C8A951'),
                    'default_w': defaults.get('w', 16),
                    'default_h': defaults.get('h', 12),
                    'categoria': meta.get('categoria', 'general'),
                    'activo': True,
                }
            )
        CardModule.objects.exclude(slug__in=slugs).update(activo=False)

    @classmethod
    def get_card_dir(cls, slug):
        """
        Devuelve el Path de la carpeta de una card dado su slug.

        Incluye proteccion contra path traversal: usa Path.name para
        limpiar el slug y verifica que la ruta resuelta este dentro de CARDS_DIR.
        """
        safe_slug = Path(slug).name
        card_dir = Path(settings.CARDS_DIR) / safe_slug
        if not str(card_dir.resolve()).startswith(str(Path(settings.CARDS_DIR).resolve())):
            return None
        return card_dir

    @classmethod
    def get_template(cls, slug):
        """Devuelve el Path al template.html de la card, o None si no existe."""
        card_dir = cls.get_card_dir(slug)
        if not card_dir:
            return None
        path = card_dir / 'template.html'
        return path if path.exists() else None

    @classmethod
    def get_style(cls, slug):
        """Devuelve el Path al style.css de la card, o None si no existe."""
        card_dir = cls.get_card_dir(slug)
        if not card_dir:
            return None
        path = card_dir / 'style.css'
        return path if path.exists() else None

    @classmethod
    def get_script(cls, slug):
        """Devuelve el Path al script.js de la card, o None si no existe."""
        card_dir = cls.get_card_dir(slug)
        if not card_dir:
            return None
        path = card_dir / 'script.js'
        return path if path.exists() else None
