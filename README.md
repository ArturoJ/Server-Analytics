# Server Analytics

Plataforma de monitorizacion de seguridad en tiempo real. Detecta ataques a servidores web, bloquea IPs automaticamente, geolocaliza el origen y notifica por Telegram.

Dashboard modular con widgets personalizables (drag-and-drop), estadisticas por pais, reglas de deteccion configurables y PWA instalable.

## Requisitos

- Ubuntu 24.04 LTS
- Python 3.10+
- Nginx (para el analizador de logs)
- UFW (opcional, para bloqueo automatico de IPs)

## Instalacion rapida

```bash
git clone https://github.com/ArturoJ/Server-Analytics.git
cd Server-Analytics
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # Editar con tus datos
python manage.py migrate
python manage.py cargar_datos
python manage.py sync_cards
python manage.py runserver
```

Abrir http://localhost:8000

## Configuracion

**Solo necesitas editar un archivo: `.env`**

```env
SECRET_KEY=genera-una-clave-secreta
DEBUG=False
ALLOWED_HOSTS=tu-dominio.com
TELEGRAM_BOT_TOKEN=tu-token        # Opcional
TELEGRAM_CHAT_ID=tu-chat-id        # Opcional
SITE_DOMAIN=https://tu-dominio.com
SITE_AUTHOR=Tu Nombre
SITE_AUTHOR_URL=https://tu-web.com
WHITELIST_IPS=127.0.0.1,::1,tu-ip
```

Para generar una SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Despliegue en produccion

### Instalacion automatica (recomendada)

En un servidor Ubuntu 24.04 limpio, como root:

```bash
curl -O https://raw.githubusercontent.com/ArturoJ/Server-Analytics/main/deploy/install.py
sudo python3 install.py
```

El script te pide los datos (dominio, IP, Telegram, email SSL) e instala todo automaticamente: dependencias, Nginx, SSL, Supervisor y firewall.

### Instalacion manual

Si prefieres hacerlo paso a paso, los archivos de ejemplo estan en `deploy/`:

```bash
deploy/nginx.conf.example       # Configuracion de Nginx
deploy/supervisor.conf.example  # Configuracion de Supervisor
deploy/install.py               # Script de instalacion automatica
```

Pasos:

1. Instalar paquetes: `apt install python3-venv nginx supervisor certbot python3-certbot-nginx ufw`
2. Clonar repo, crear venv, `pip install -r requirements.txt`
3. Copiar `.env.example` a `.env` y rellenar
4. `python manage.py migrate && python manage.py cargar_datos && python manage.py sync_cards && python manage.py collectstatic`
5. Configurar Nginx y Supervisor con los `.example` de `deploy/`
6. `certbot --nginx -d tu-dominio.com`
7. `supervisorctl start all`

## Como funciona

### Deteccion de ataques

El daemon `analizar_logs` lee el access log de Nginx cada 30 segundos y aplica las reglas de deteccion de la base de datos. Cuando una IP supera el umbral:

1. Crea un registro de bloqueo con las rutas solicitadas
2. Bloquea la IP con UFW
3. Geolocaliza el origen con base de datos local (DB-IP)
4. Envia notificacion por Telegram

### Dashboard modular

7 widgets disponibles organizados por categorias:

| Widget | Categoria | Descripcion |
|--------|-----------|-------------|
| KPI | Metricas | IPs bloqueadas, peticiones, paises, IP top, visitantes |
| Ataques por Hora | Graficos | Distribucion horaria de bloqueos |
| Tipo de Ataque | Graficos | Doughnut por tipo (escaneo, exceso, fuerza bruta) |
| Top 5 IPs | Graficos | IPs con mas peticiones bloqueadas |
| Paises | Tablas | Ranking de paises por ataques |
| Reglas | Tablas | Estado de reglas de deteccion |
| Ultimos Bloqueos | Tablas | Tabla filtrable con exportacion CSV |

El layout se guarda en el navegador (localStorage). Cada usuario personaliza su dashboard sin afectar a los demas.

### Geolocalizacion

Usa una base de datos local de DB-IP (formato MMDB). Se descarga automaticamente por HTTPS y se actualiza cada 24 horas. Sin dependencia de APIs externas en tiempo real.

## Estructura del proyecto

```
monitor/
    models.py              8 modelos documentados
    urls.py                Rutas URL
    admin.py               Panel de administracion
    middleware.py           Rate limiting por IP
    context_processors.py  Variables de configuracion en templates
    views/                 Paginas HTML
        dashboard.py       Dashboard modular
        bloqueos.py        Lista y detalle de IP
        estadisticas.py    Estadisticas por pais
        servidores.py      Lista de servidores
        reglas.py          Reglas de deteccion
        seo.py             Robots, sitemap, PWA, honeypot
    api/                   Endpoints JSON (solo lectura)
        dashboard.py       KPIs, graficos, ultimos bloqueos
        bloqueos.py        Listado paginado + CSV
        estadisticas.py    Ranking por pais
        reglas.py          Reglas con stats del dia
    services/              Logica backend
        cards.py           Descubrimiento de cards desde disco
        geoip.py           Geolocalizacion local (DB-IP)
    tests/                 102 tests
        models/            Tests de cada modelo
        views/             Tests de cada pagina
        api/               Tests de cada endpoint
        test_seguridad.py  SQL injection, XSS, path traversal
        test_middleware.py  Rate limiting
        test_services.py   CardRegistry, geoip, sanitizacion
    management/commands/
        analizar_logs.py   Daemon de deteccion en tiempo real
        cargar_datos.py    Datos semilla
        sync_cards.py      Sincronizar cards desde disco
cards/                     7 modulos de widgets
    kpi/                   card.json + template.html + style.css + script.js
    grafico_hora/
    grafico_tipo/
    top_ips/
    paises/
    reglas/
    tabla_bloqueos/
templates/                 12 templates HTML
static/                    CSS, JS, iconos PWA
deploy/                    Configs de ejemplo para Nginx y Supervisor
```

## Seguridad

- CSP estricto con nonces (`default-src 'none'`)
- Subresource Integrity en scripts externos
- HSTS con preload
- Rate limiting por IP (60 req/min)
- Validacion de todos los inputs
- Sanitizacion de rutas contra XSS persistente
- Templates de error custom (no revelan el framework)
- Honeypot de contacto para atraer bots
- Geolocalización local por HTTPS (sin MITM)

## Tests

```bash
python manage.py test monitor
```

102 tests cubriendo modelos, endpoints, vistas, seguridad, middleware y servicios.

## API

Todos los endpoints son de solo lectura (GET) y devuelven JSON.

| Endpoint | Descripcion |
|----------|-------------|
| `/api/dashboard/` | KPIs, graficos, ultimos bloqueos |
| `/api/bloqueos/?page=1&motivo=escaneo&pais=US` | Listado paginado con filtros |
| `/api/bloqueos/?formato=csv` | Exportacion CSV |
| `/api/estadisticas/paises/` | Ranking de paises |
| `/api/reglas/` | Reglas de deteccion con stats del dia |

## Management commands

| Comando | Descripcion |
|---------|-------------|
| `analizar_logs --daemon --bloquear` | Daemon de deteccion en tiempo real |
| `cargar_datos` | Carga servidor, reglas y bloqueos de ejemplo |
| `sync_cards` | Sincroniza cards desde disco y crea dashboard por defecto |

## Licencia

MIT
