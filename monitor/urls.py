"""Rutas URL de la app monitor: paginas HTML, endpoints API, SEO y PWA."""
from django.urls import path
from . import views
from . import api

urlpatterns = [
    # Paginas HTML
    path('', views.dashboard, name='dashboard'),
    path('bloqueos/', views.bloqueos_lista, name='bloqueos'),
    path('bloqueos/<str:ip>/', views.detalle_ip, name='detalle_ip'),
    path('estadisticas/paises/', views.estadisticas_paises, name='estadisticas_paises'),
    path('servidores/', views.servidores_lista, name='servidores'),
    path('reglas/', views.reglas_lista, name='reglas'),

    # API endpoints (solo lectura, JSON)
    path('api/dashboard/', api.api_dashboard, name='api_dashboard'),
    path('api/bloqueos/', api.api_bloqueos, name='api_bloqueos'),
    path('api/estadisticas/paises/', api.api_estadisticas_paises, name='api_estadisticas_paises'),
    path('api/reglas/', api.api_reglas, name='api_reglas'),

    # SEO, PWA y honeypot
    path('sw.js', views.service_worker, name='service_worker'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
    path('sitemap.xml', views.sitemap_xml, name='sitemap_xml'),
    path('contacto/', views.contacto, name='contacto'),
]
