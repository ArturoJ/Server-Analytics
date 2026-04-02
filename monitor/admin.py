"""Configuracion del panel de administracion de Django para los modelos de monitor."""
from django.contrib import admin
from .models import Servidor, Bloqueo, ReglaDeteccion, MetricaDiaria, Dashboard, CardModule, CardInstance, Visita


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'ip', 'estado', 'fecha_alta']
    list_filter = ['estado']
    search_fields = ['nombre', 'ip']


@admin.register(Bloqueo)
class BloqueoAdmin(admin.ModelAdmin):
    list_display = ['ip', 'pais', 'motivo', 'peticiones', 'fecha_bloqueo', 'activo']
    list_filter = ['motivo', 'activo', 'servidor']
    search_fields = ['ip', 'pais']
    date_hierarchy = 'fecha_bloqueo'


@admin.register(ReglaDeteccion)
class ReglaDeteccionAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'umbral_peticiones', 'ventana_minutos', 'activa']
    list_filter = ['tipo', 'activa']


@admin.register(MetricaDiaria)
class MetricaDiariaAdmin(admin.ModelAdmin):
    list_display = ['servidor', 'fecha', 'total_bloqueos', 'total_peticiones', 'pais_top']
    list_filter = ['servidor']
    date_hierarchy = 'fecha'


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ['ip', 'peticiones', 'primera_visita', 'ultima_visita']
    search_fields = ['ip']


@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'creado', 'modificado']


@admin.register(CardModule)
class CardModuleAdmin(admin.ModelAdmin):
    list_display = ['slug', 'nombre', 'categoria', 'activo']
    list_filter = ['categoria', 'activo']


@admin.register(CardInstance)
class CardInstanceAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'module', 'dashboard', 'grid_x', 'grid_y']
    list_filter = ['module', 'dashboard']
