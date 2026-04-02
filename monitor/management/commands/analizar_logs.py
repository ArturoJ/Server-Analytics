"""
Analizador de logs de nginx en tiempo real.

Este command lee /var/log/nginx/access.log cada 30 segundos,
aplica las ReglaDeteccion de la base de datos, y cuando una IP
supera el umbral:
    1. Crea un registro Bloqueo con las rutas solicitadas
    2. Bloquea la IP con UFW (si se usa --bloquear)
    3. Geolocaliza la IP con la BD local de DB-IP
    4. Envia notificacion por Telegram

Ademas, registra visitantes unicos (IPs con peticiones 200/301/302
a paginas reales) en el modelo Visita.

Auto-actualiza la BD de geolocalizacion cada 24 horas.

Uso:
    python manage.py analizar_logs --daemon --bloquear
    python manage.py analizar_logs --daemon --bloquear --whitelist 1.2.3.4 5.6.7.8
"""
import logging
import re
import time
import subprocess
import urllib.error
import urllib.request
import urllib.parse
from collections import defaultdict
from datetime import timedelta

logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.conf import settings
from django.utils.html import strip_tags

from django.db import models as db_models
from monitor.models import Servidor, Bloqueo, ReglaDeteccion, Visita
from monitor.services import buscar_pais, necesita_actualizar, actualizar_db


def sanitizar_ruta(texto):
    """
    Limpia una ruta HTTP para almacenarla de forma segura.

    Elimina tags HTML (contra XSS), comillas y caracteres no imprimibles.
    Trunca a 200 caracteres.
    """
    limpio = strip_tags(texto)
    limpio = limpio.replace('"', '').replace("'", '').replace('`', '')
    limpio = re.sub(r'[^\x20-\x7E]', '', limpio)
    return limpio[:200]


LOG_PATH = "/var/log/nginx/access.log"
INTERVALO = 30
CACHE_GEO = {}

WHITELIST = getattr(settings, 'WHITELIST_IPS', {'127.0.0.1', '::1'})

RUTAS_IGNORADAS = re.compile(r'^/(static/|api/|favicon\.ico)')

REGEX_NGINX = re.compile(
    r'^(?P<ip>[\d.:a-fA-F]+)\S*\s+-\s+-\s+'
    r'\[(?P<fecha>[^\]]+)\]\s+'
    r'"(?P<metodo>\S+)\s+(?P<ruta>\S+)\s+\S+"\s+'
    r'(?P<codigo>\d{3})\s+'
)

CODIGOS_SOSPECHOSOS = {404, 403, 400, 401}


def geoip(ip):
    """Busca el pais de una IP, usando cache en memoria para evitar consultas repetidas."""
    if ip in CACHE_GEO:
        return CACHE_GEO[ip]
    resultado = buscar_pais(ip)
    CACHE_GEO[ip] = resultado
    return resultado


def enviar_telegram(token, chat_id, mensaje):
    """Envia un mensaje por Telegram. Registra el error si falla."""
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    datos = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": mensaje,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=datos)
        urllib.request.urlopen(req, timeout=10)
    except (urllib.error.URLError, OSError) as e:
        logger.warning(f'Error enviando Telegram: {e}')


class Command(BaseCommand):
    help = 'Analiza logs de nginx y registra bloqueos en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument('--daemon', action='store_true', help='Ejecutar en bucle continuo')
        parser.add_argument('--bloquear', action='store_true', help='Bloquear IPs con ufw')
        parser.add_argument('--log', default=LOG_PATH, help='Ruta al access log de nginx')
        parser.add_argument('--whitelist', nargs='*', default=[], help='IPs adicionales en whitelist')

    def handle(self, *args, **options):
        """Punto de entrada del command. Configura y arranca el bucle principal."""
        log_path = options['log']
        daemon = options['daemon']
        bloquear_ufw = options['bloquear']
        whitelist = WHITELIST | set(options['whitelist'])

        servidor = Servidor.objects.first()
        if not servidor:
            self.stderr.write('No hay servidores en la BD. Ejecuta cargar_datos primero.')
            return

        reglas = list(ReglaDeteccion.objects.filter(activa=True))
        reglas_compiladas = []
        for regla in reglas:
            patrones = [p.strip() for p in regla.patron.split('|') if p.strip()]
            reglas_compiladas.append({
                'regla': regla,
                'patrones': [re.compile(p, re.IGNORECASE) for p in patrones],
                'umbral': regla.umbral_peticiones,
                'ventana': regla.ventana_minutos,
                'tipo': regla.tipo,
            })

        self.stdout.write(f'Servidor: {servidor.nombre}')
        self.stdout.write(f'Reglas activas: {len(reglas_compiladas)}')
        self.stdout.write(f'Log: {log_path}')
        self.stdout.write(f'UFW: {"SI" if bloquear_ufw else "NO"}')
        self.stdout.write(f'Modo: {"DAEMON" if daemon else "UNA PASADA"}')

        telegram_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        telegram_chat = getattr(settings, 'TELEGRAM_CHAT_ID', '')

        try:
            with open(log_path, 'r') as f:
                f.seek(0, 2)
                posicion = f.tell()
        except FileNotFoundError:
            self.stderr.write(f'No se encuentra {log_path}')
            return
        except PermissionError:
            self.stderr.write(f'Sin permisos para leer {log_path}')
            return

        ips_procesadas = set(
            Bloqueo.objects.filter(
                fecha_bloqueo__gte=timezone.now() - timedelta(hours=24)
            ).values_list('ip', flat=True)
        )

        self._actualizar_geoip()

        self.stdout.write(self.style.SUCCESS('Analizador iniciado'))
        enviar_telegram(telegram_token, telegram_chat, '\u2705 <b>Server Analytics</b>\nAnalizador de logs iniciado')

        while True:
            self._actualizar_geoip()

            posicion, nuevos = self._procesar(
                log_path, posicion, reglas_compiladas, servidor,
                whitelist, ips_procesadas, bloquear_ufw,
                telegram_token, telegram_chat,
            )
            if nuevos:
                self.stdout.write(f'{timezone.now().strftime("%H:%M:%S")} | {nuevos} bloqueos registrados')

            if not daemon:
                break
            time.sleep(INTERVALO)

    def _actualizar_geoip(self):
        """Descarga la BD de geolocalizacion si no existe o tiene mas de 24h."""
        if not necesita_actualizar():
            return
        try:
            self.stdout.write('Actualizando base de datos GeoIP...')
            actualizar_db()
            self.stdout.write(self.style.SUCCESS('GeoIP actualizada'))
        except (urllib.error.URLError, OSError) as e:
            self.stderr.write(f'Error actualizando GeoIP: {e}')

    def _procesar(self, log_path, posicion, reglas, servidor, whitelist, ips_procesadas, bloquear_ufw, tg_token, tg_chat):
        """
        Lee las lineas nuevas del log y las procesa.

        Hace dos cosas en paralelo:
        1. Detecta ataques segun las reglas y crea bloqueos
        2. Registra visitantes unicos (peticiones 200/301/302 a paginas reales)

        Returns:
            tuple: (nueva_posicion_del_fichero, numero_de_bloqueos_nuevos)
        """
        try:
            with open(log_path, 'r') as f:
                f.seek(0, 2)
                tam = f.tell()
                if tam < posicion:
                    posicion = 0
                f.seek(posicion)
                lineas = f.readlines()
                nueva_pos = f.tell()
        except (FileNotFoundError, PermissionError, OSError) as e:
            self.stderr.write(f'Error leyendo log: {e}')
            return posicion, 0

        if not lineas:
            return nueva_pos, 0

        ahora = timezone.now()
        hits_por_regla = defaultdict(lambda: defaultdict(int))
        rutas_por_ip = defaultdict(list)
        visitantes_vistos = defaultdict(int)

        for linea in lineas:
            match = REGEX_NGINX.match(linea)
            if not match:
                continue

            ip = match.group('ip')
            codigo = int(match.group('codigo'))
            ruta = match.group('ruta')

            # Conteo de visitantes: IPs unicas con peticiones exitosas a paginas reales
            if ip not in whitelist and codigo in (200, 301, 302) and not RUTAS_IGNORADAS.match(ruta):
                visitantes_vistos[ip] += 1

            if ip in whitelist or ip in ips_procesadas:
                continue

            # Deteccion de ataques segun reglas activas
            for rc in reglas:
                detected = False
                if rc['tipo'] == 'escaneo':
                    if any(p.search(ruta) for p in rc['patrones']):
                        hits_por_regla[rc['regla'].pk][(ip, rc['regla'].pk)] += 1
                        detected = True
                elif rc['tipo'] == 'exceso':
                    if not RUTAS_IGNORADAS.match(ruta):
                        hits_por_regla[rc['regla'].pk][(ip, rc['regla'].pk)] += 1
                        detected = True
                elif rc['tipo'] == 'fuerza_bruta':
                    if any(p.search(ruta) for p in rc['patrones']) and codigo in CODIGOS_SOSPECHOSOS:
                        hits_por_regla[rc['regla'].pk][(ip, rc['regla'].pk)] += 1
                        detected = True
                if detected:
                    entrada = f'{codigo} {sanitizar_ruta(ruta)}'
                    if entrada not in rutas_por_ip[ip]:
                        rutas_por_ip[ip].append(entrada)

        # Crear bloqueos para IPs que superan el umbral
        nuevos = 0
        reglas_dict = {rc['regla'].pk: rc for rc in reglas}

        for regla_pk, ip_hits in hits_por_regla.items():
            rc = reglas_dict[regla_pk]
            for (ip, _), count in ip_hits.items():
                if count < rc['umbral']:
                    continue
                if ip in ips_procesadas:
                    continue

                pais, codigo_pais = geoip(ip)

                Bloqueo.objects.create(
                    servidor=servidor,
                    regla=rc['regla'],
                    ip=ip,
                    pais=pais,
                    codigo_pais=codigo_pais,
                    motivo=rc['tipo'],
                    peticiones=count,
                    rutas=rutas_por_ip.get(ip, [])[:50],
                    fecha_bloqueo=ahora,
                    activo=True,
                )

                ips_procesadas.add(ip)
                nuevos += 1

                if bloquear_ufw:
                    try:
                        subprocess.run(
                            ['ufw', 'insert', '1', 'deny', 'from', ip, 'to', 'any'],
                            capture_output=True, text=True, timeout=10,
                        )
                    except (subprocess.SubprocessError, OSError) as e:
                        self.stderr.write(f'Error bloqueando IP {ip} con ufw: {e}')

                enviar_telegram(tg_token, tg_chat,
                    f'\U0001f6ab <b>BLOQUEO</b>\n'
                    f'\U0001f4cd IP: {ip}\n'
                    f'\U0001f30d Pais: {pais} {codigo_pais}\n'
                    f'\u26a0\ufe0f Motivo: {rc["regla"].get_tipo_display()}\n'
                    f'\U0001f4ca Peticiones: {count}\n'
                    f'\U0001f4cb Regla: {rc["regla"].nombre}'
                )

        # Registrar visitantes unicos
        for ip, pet in visitantes_vistos.items():
            visita, created = Visita.objects.get_or_create(ip=ip)
            if not created:
                Visita.objects.filter(pk=visita.pk).update(
                    peticiones=db_models.F('peticiones') + pet,
                )

        return nueva_pos, nuevos
