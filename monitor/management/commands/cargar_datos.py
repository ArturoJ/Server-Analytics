"""Carga datos semilla: servidor, reglas de deteccion y 30 bloqueos de ejemplo."""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from monitor.models import Servidor, Bloqueo, ReglaDeteccion, MetricaDiaria


DATOS = [
    {'h':'22:02','ip':'114.119.135.196','m':'escaneo','r':10,'p':'China','c':'CN'},
    {'h':'22:56','ip':'61.245.11.87','m':'escaneo','r':36,'p':'India','c':'IN'},
    {'h':'22:59','ip':'34.27.168.155','m':'escaneo','r':18,'p':'EEUU','c':'US'},
    {'h':'23:26','ip':'114.119.137.28','m':'escaneo','r':9,'p':'China','c':'CN'},
    {'h':'00:46','ip':'23.101.4.52','m':'escaneo','r':25,'p':'EEUU','c':'US'},
    {'h':'00:49','ip':'114.119.148.60','m':'escaneo','r':10,'p':'China','c':'CN'},
    {'h':'01:22','ip':'46.249.101.24','m':'escaneo','r':12,'p':'Alemania','c':'DE'},
    {'h':'02:13','ip':'114.119.128.253','m':'escaneo','r':6,'p':'China','c':'CN'},
    {'h':'02:21','ip':'64.225.75.246','m':'exceso','r':25,'p':'EEUU','c':'US'},
    {'h':'06:53','ip':'20.220.232.240','m':'escaneo','r':63,'p':'EEUU','c':'US'},
    {'h':'07:20','ip':'114.119.134.95','m':'escaneo','r':10,'p':'China','c':'CN'},
    {'h':'07:24','ip':'20.63.96.180','m':'escaneo','r':67,'p':'EEUU','c':'US'},
    {'h':'11:43','ip':'172.70.243.60','m':'escaneo','r':46,'p':'Holanda','c':'NL'},
    {'h':'11:43','ip':'172.70.243.207','m':'escaneo','r':36,'p':'Holanda','c':'NL'},
    {'h':'11:43','ip':'172.70.243.208','m':'escaneo','r':19,'p':'Holanda','c':'NL'},
    {'h':'11:43','ip':'172.70.243.66','m':'escaneo','r':42,'p':'Holanda','c':'NL'},
    {'h':'11:43','ip':'172.70.242.126','m':'escaneo','r':19,'p':'Holanda','c':'NL'},
    {'h':'11:43','ip':'172.70.242.127','m':'escaneo','r':14,'p':'Holanda','c':'NL'},
    {'h':'11:56','ip':'4.204.200.32','m':'escaneo','r':58,'p':'EEUU','c':'US'},
    {'h':'12:15','ip':'8.229.218.93','m':'escaneo','r':18,'p':'China','c':'CN'},
    {'h':'12:26','ip':'20.107.195.165','m':'escaneo','r':10,'p':'EEUU','c':'US'},
    {'h':'12:57','ip':'118.145.100.92','m':'escaneo','r':6,'p':'China','c':'CN'},
    {'h':'15:23','ip':'62.171.162.87','m':'escaneo','r':38,'p':'Alemania','c':'DE'},
    {'h':'15:41','ip':'114.119.154.189','m':'escaneo','r':10,'p':'China','c':'CN'},
    {'h':'18:17','ip':'134.209.201.63','m':'escaneo','r':18,'p':'EEUU','c':'US'},
    {'h':'18:41','ip':'178.128.32.223','m':'escaneo','r':18,'p':'Holanda','c':'NL'},
    {'h':'20:00','ip':'157.230.254.157','m':'escaneo','r':18,'p':'EEUU','c':'US'},
    {'h':'21:13','ip':'114.119.155.200','m':'escaneo','r':10,'p':'China','c':'CN'},
    {'h':'21:53','ip':'172.235.168.35','m':'exceso','r':64,'p':'EEUU','c':'US'},
    {'h':'22:32','ip':'161.178.132.46','m':'escaneo','r':26,'p':'EEUU','c':'US'},
]


class Command(BaseCommand):
    help = 'Carga los 30 bloqueos del Post 1 como datos semilla'

    def handle(self, *args, **options):
        servidor, created = Servidor.objects.get_or_create(
            nombre='vps-production-01',
            defaults={'ip': '0.0.0.0', 'sistema_operativo': 'Ubuntu 22.04 LTS'},
        )
        self.stdout.write(f'Servidor: {servidor.nombre} ({"creado" if created else "existente"})')

        regla_scan, _ = ReglaDeteccion.objects.get_or_create(
            nombre='scan_vuln_01',
            defaults={'patron': r'/wp-admin|/phpmyadmin|/.env|/xmlrpc', 'tipo': 'escaneo',
                      'umbral_peticiones': 5, 'ventana_minutos': 5,
                      'descripcion': 'Detecta peticiones a rutas típicas de exploits'},
        )
        regla_excess, _ = ReglaDeteccion.objects.get_or_create(
            nombre='excess_req_01',
            defaults={'patron': '.*', 'tipo': 'exceso',
                      'umbral_peticiones': 50, 'ventana_minutos': 1,
                      'descripcion': 'Exceso de peticiones en poco tiempo'},
        )
        ReglaDeteccion.objects.get_or_create(
            nombre='brute_force_01',
            defaults={'patron': r'/login|/admin|/api/auth', 'tipo': 'fuerza_bruta',
                      'umbral_peticiones': 10, 'ventana_minutos': 2,
                      'descripcion': 'Intentos de fuerza bruta contra login'},
        )
        ReglaDeteccion.objects.get_or_create(
            nombre='bot_detect_01',
            defaults={'patron': r'User-Agent:.*(bot|crawler|spider)', 'tipo': 'custom',
                      'umbral_peticiones': 20, 'ventana_minutos': 10, 'activa': False,
                      'descripcion': 'Detecta bots por User-Agent (desactivada)'},
        )

        hoy = timezone.now().date()
        count = 0
        for d in DATOS:
            hora, minuto = d['h'].split(':')
            fecha = timezone.make_aware(datetime(hoy.year, hoy.month, hoy.day, int(hora), int(minuto)))
            regla = regla_excess if d['m'] == 'exceso' else regla_scan
            Bloqueo.objects.get_or_create(
                servidor=servidor, ip=d['ip'], fecha_bloqueo=fecha,
                defaults={
                    'regla': regla, 'pais': d['p'], 'codigo_pais': d['c'],
                    'motivo': d['m'], 'peticiones': d['r'],
                },
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'{count} bloqueos procesados.'))
