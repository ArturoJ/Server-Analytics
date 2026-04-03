"""
Modelos de datos de Server Analytics.

8 modelos organizados en 3 bloques:
- Seguridad: Servidor, ReglaDeteccion, Bloqueo, MetricaDiaria
- Visitantes: Visita
- Dashboard modular: Dashboard, CardModule, CardInstance
"""
import uuid
from django.db import models
from django.core.validators import MinValueValidator, validate_ipv46_address


ESTADOS_SERVIDOR = (
    ('activo', 'Activo'),
    ('inactivo', 'Inactivo'),
    ('mantenimiento', 'Mantenimiento'),
)

MOTIVOS_BLOQUEO = (
    ('escaneo', 'Escaneo de vulnerabilidades'),
    ('exceso', 'Exceso de peticiones'),
    ('fuerza_bruta', 'Fuerza bruta'),
)

TIPOS_REGLA = (
    ('escaneo', 'Escaneo'),
    ('fuerza_bruta', 'Fuerza bruta'),
    ('exceso', 'Exceso'),
    ('custom', 'Custom'),
)


# ============================================================
# Bloque 1: Seguridad
# ============================================================

class Servidor(models.Model):
    """Servidor monitorizado. Cada bloqueo y metrica pertenece a un servidor."""
    nombre = models.CharField(max_length=100, unique=True)
    ip = models.CharField(max_length=45, validators=[validate_ipv46_address])
    hostname = models.CharField(max_length=200, blank=True)
    sistema_operativo = models.CharField(max_length=50, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_SERVIDOR, default='activo')
    fecha_alta = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Servidores'

    def __str__(self):
        return self.nombre


class ReglaDeteccion(models.Model):
    """
    Regla para detectar ataques en los logs de nginx.

    El campo 'patron' contiene expresiones regulares separadas por '|'.
    Cuando una IP supera 'umbral_peticiones' en 'ventana_minutos',
    se crea un Bloqueo automaticamente.
    Si 'metodo' esta definido, solo cuenta peticiones con ese metodo HTTP.
    """
    METODOS_HTTP = (
        ('', 'Cualquiera'),
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('DELETE', 'DELETE'),
    )

    nombre = models.CharField(max_length=100)
    patron = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPOS_REGLA)
    metodo = models.CharField(max_length=10, choices=METODOS_HTTP, blank=True, default='')
    umbral_peticiones = models.IntegerField(default=10)
    ventana_minutos = models.IntegerField(default=5)
    activa = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Regla de detección'
        verbose_name_plural = 'Reglas de detección'

    def __str__(self):
        return self.nombre


class Bloqueo(models.Model):
    """
    Registro de una IP bloqueada por el sistema de deteccion.

    Contiene la IP, pais (geolocalizado con DB-IP local), motivo,
    numero de peticiones y las rutas que solicito (sanitizadas contra XSS).
    """
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='bloqueos')
    regla = models.ForeignKey(ReglaDeteccion, on_delete=models.SET_NULL, null=True, blank=True)
    ip = models.CharField(max_length=45, db_index=True)
    pais = models.CharField(max_length=60, blank=True)
    codigo_pais = models.CharField(max_length=2, blank=True)
    motivo = models.CharField(max_length=30, choices=MOTIVOS_BLOQUEO)
    peticiones = models.IntegerField(validators=[MinValueValidator(1)])
    rutas = models.JSONField(default=list, blank=True)
    fecha_bloqueo = models.DateTimeField(db_index=True)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_bloqueo']

    def __str__(self):
        return f'{self.ip} ({self.get_motivo_display()})'


class MetricaDiaria(models.Model):
    """Metricas agregadas por dia y servidor. Se usa para graficos historicos."""
    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name='metricas')
    fecha = models.DateField(db_index=True)
    total_bloqueos = models.IntegerField(default=0)
    total_peticiones = models.IntegerField(default=0)
    pais_top = models.CharField(max_length=60, blank=True)
    ip_top = models.CharField(max_length=45, blank=True)
    por_tipo = models.JSONField(default=dict)
    por_pais = models.JSONField(default=dict)

    class Meta:
        unique_together = ['servidor', 'fecha']
        verbose_name = 'Métrica diaria'
        verbose_name_plural = 'Métricas diarias'

    def __str__(self):
        return f'{self.servidor} - {self.fecha}'


# ============================================================
# Bloque 2: Visitantes
# ============================================================

class Visita(models.Model):
    """
    Visitante unico identificado por IP.

    Se registra automaticamente desde el daemon analizar_logs
    al detectar peticiones a paginas reales (200/301/302).
    No almacena datos personales, solo la IP y contadores.
    """
    ip = models.CharField(max_length=45, unique=True)
    primera_visita = models.DateTimeField(auto_now_add=True)
    ultima_visita = models.DateTimeField(auto_now=True)
    peticiones = models.IntegerField(default=1)

    class Meta:
        ordering = ['-ultima_visita']

    def __str__(self):
        return self.ip


# ============================================================
# Bloque 3: Dashboard modular
# ============================================================

class Dashboard(models.Model):
    """Contenedor de cards. Por defecto se usa uno solo (pk=1)."""
    nombre = models.CharField(max_length=100)
    creado = models.DateTimeField(auto_now_add=True)
    modificado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-modificado']

    def __str__(self):
        return self.nombre


class CardModule(models.Model):
    """
    Tipo de widget disponible en el catalogo del dashboard.

    Cada modulo corresponde a una carpeta en cards/ con:
    card.json (metadatos), template.html, style.css y script.js.
    El CardRegistry los descubre automaticamente desde disco.
    """
    slug = models.SlugField(unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, default='')
    color = models.CharField(max_length=7, default='#C8A951')
    default_w = models.IntegerField(default=16)
    default_h = models.IntegerField(default=12)
    categoria = models.CharField(max_length=50, default='general', blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class CardInstance(models.Model):
    """
    Instancia de un widget colocada en un dashboard.

    Almacena la posicion (grid_x, grid_y), tamano (grid_w, grid_h),
    configuracion especifica (config JSON) y un label personalizable.
    """
    dashboard = models.ForeignKey(Dashboard, on_delete=models.CASCADE, related_name='cards')
    module = models.ForeignKey(CardModule, on_delete=models.CASCADE, related_name='instances')
    instance_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    label = models.CharField(max_length=100, blank=True, default='')
    config = models.JSONField(default=dict, blank=True)
    grid_x = models.IntegerField(default=0)
    grid_y = models.IntegerField(default=0)
    grid_w = models.IntegerField(default=16)
    grid_h = models.IntegerField(default=12)
    z_index = models.IntegerField(default=0)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['z_index', 'creado']

    @property
    def display_name(self):
        """Devuelve el label personalizado o el nombre del modulo."""
        return self.label or self.module.nombre

    def __str__(self):
        return f'{self.display_name}:{self.instance_id.hex[:8]}'
