#!/usr/bin/env python3
"""
Server Analytics — Script de instalacion automatica via SSH.

Se ejecuta desde tu PC local, se conecta al servidor por SSH
y despliega todo automaticamente.

Uso:
    1. Copiar .env.example a .env y rellenar tus datos
    2. Ejecutar: python3 deploy/install.py

Requisito en el servidor: Ubuntu 24.04 LTS
"""
import os
import subprocess
import sys
import getpass


# ============================================================
# Colores
# ============================================================

RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
NC = '\033[0m'


def log(msg):
    print(f'{GREEN}[OK]{NC} {msg}')


def warn(msg):
    print(f'{YELLOW}[!]{NC} {msg}')


def err(msg):
    print(f'{RED}[ERROR]{NC} {msg}')
    sys.exit(1)


def step(msg):
    print(f'\n{CYAN}=== {msg} ==={NC}')


# ============================================================
# Lectura de .env
# ============================================================

def leer_env(path):
    """Lee un archivo .env y devuelve un diccionario."""
    config = {}
    with open(path) as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith('#'):
                continue
            if '=' not in linea:
                continue
            clave, valor = linea.split('=', 1)
            config[clave.strip()] = valor.strip()
    return config


# ============================================================
# SSH
# ============================================================

class SSH:
    """Ejecuta comandos en un servidor remoto via SSH."""

    def __init__(self, host, user, port=22, password=None):
        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self._ssh_base = ['ssh', '-o', 'StrictHostKeyChecking=accept-new', '-p', str(port)]
        if password:
            self._ssh_base = ['sshpass', '-p', password] + self._ssh_base
        self._scp_base = ['scp', '-o', 'StrictHostKeyChecking=accept-new', '-P', str(port)]
        if password:
            self._scp_base = ['sshpass', '-p', password] + self._scp_base

    def run(self, cmd, check=True, quiet=False):
        """Ejecuta un comando en el servidor remoto con salida en tiempo real."""
        full_cmd = self._ssh_base + [f'{self.user}@{self.host}', cmd]
        if quiet:
            result = subprocess.run(full_cmd, capture_output=True, text=True)
        else:
            result = subprocess.run(full_cmd, text=True)
        if check and result.returncode != 0:
            err(f'Fallo el comando remoto: {cmd}')
        return result

    def run_quiet(self, cmd):
        """Ejecuta sin mostrar salida (para comprobaciones)."""
        return self.run(cmd, check=False, quiet=True)

    def upload(self, local_path, remote_path):
        """Sube un archivo al servidor con progreso visible."""
        full_cmd = self._scp_base + [local_path, f'{self.user}@{self.host}:{remote_path}']
        result = subprocess.run(full_cmd, text=True)
        if result.returncode != 0:
            err(f'Error subiendo {local_path}')

    def test(self):
        """Comprueba que la conexion SSH funciona."""
        result = self.run_quiet('echo ok')
        return result.returncode == 0 and 'ok' in result.stdout


# ============================================================
# Configuracion
# ============================================================

def cargar_configuracion():
    step('Leyendo configuracion desde .env')

    script_dir = os.path.dirname(os.path.abspath(__file__))
    proyecto_dir = os.path.dirname(script_dir)
    env_path = os.path.join(proyecto_dir, '.env')

    if not os.path.exists(env_path):
        err('No se encuentra .env. Copia .env.example a .env y rellena tus datos.')

    env = leer_env(env_path)

    # Validar campos obligatorios
    domain = env.get('ALLOWED_HOSTS', '')
    if not domain or domain == 'tu-dominio.com':
        err('ALLOWED_HOSTS no esta configurado en .env')

    ssh_host = env.get('SSH_HOST', '')
    if not ssh_host or ssh_host == 'IP-DE-TU-SERVIDOR':
        err('SSH_HOST no esta configurado en .env')

    deploy_email = env.get('DEPLOY_EMAIL', '')
    if not deploy_email or deploy_email == 'tu-email@ejemplo.com':
        err('DEPLOY_EMAIL no esta configurado en .env')

    deploy_method = env.get('DEPLOY_METHOD', 'upload')
    deploy_repo = env.get('DEPLOY_REPO', '')
    if deploy_method == 'repo' and (not deploy_repo or 'tu-usuario' in deploy_repo):
        err('DEPLOY_REPO no esta configurado en .env')

    deploy_user = env.get('DEPLOY_USER', 'serveranalytics')

    config = {
        'domain': domain.split(',')[0],
        'author': env.get('SITE_AUTHOR', 'Server Analytics'),
        'author_url': env.get('SITE_AUTHOR_URL', ''),
        'tg_token': env.get('TELEGRAM_BOT_TOKEN', ''),
        'tg_chat': env.get('TELEGRAM_CHAT_ID', ''),
        'whitelist': env.get('WHITELIST_IPS', '127.0.0.1,::1'),
        'user': deploy_user,
        'email': deploy_email,
        'repo': deploy_repo,
        'method': deploy_method,
        'secret_key': env.get('SECRET_KEY', ''),
        'api_key': env.get('API_KEY', ''),
        'ssh_host': ssh_host,
        'ssh_user': env.get('SSH_USER', 'root'),
        'ssh_port': env.get('SSH_PORT', '22'),
        'ssh_password': env.get('SSH_PASSWORD', ''),
        'proyecto_dir': proyecto_dir,
    }

    config['app_dir'] = f'/home/{config["user"]}/proyectodir'
    config['venv'] = f'{config["app_dir"]}/venv'

    metodo_label = 'Subir proyecto local' if deploy_method == 'upload' else f'Clonar desde {deploy_repo}'

    print(f'\n-----------------------------------')
    print(f' Servidor:   {config["ssh_user"]}@{config["ssh_host"]}:{config["ssh_port"]}')
    print(f' Dominio:    {config["domain"]}')
    print(f' Autor:      {config["author"]}')
    print(f' Telegram:   {"Si" if config["tg_token"] else "No"}')
    print(f' Usuario:    {config["user"]}')
    print(f' Directorio: {config["app_dir"]}')
    print(f' Metodo:     {metodo_label}')
    print(f' Email SSL:  {config["email"]}')
    print(f'-----------------------------------')

    resp = input('\nContinuar con la instalacion? (s/n): ').strip()
    if resp != 's':
        sys.exit(0)

    return config


# ============================================================
# Conexion SSH
# ============================================================

def conectar(config):
    step('Conectando al servidor')

    password = config.get('ssh_password', '')

    # Si hay contraseña en .env, usarla directamente
    if password:
        # Verificar que sshpass esta instalado
        result = subprocess.run(['which', 'sshpass'], capture_output=True)
        if result.returncode != 0:
            err('SSH_PASSWORD requiere sshpass. Instalar: sudo apt install sshpass')

        ssh = SSH(
            host=config['ssh_host'],
            user=config['ssh_user'],
            port=int(config['ssh_port']),
            password=password,
        )
        if ssh.test():
            log(f'Conectado a {config["ssh_host"]} con contraseña')
            return ssh
        err('Contraseña SSH incorrecta o servidor inaccesible')

    # Sin contraseña, probar clave SSH
    ssh = SSH(
        host=config['ssh_host'],
        user=config['ssh_user'],
        port=int(config['ssh_port']),
    )
    if ssh.test():
        log(f'Conectado a {config["ssh_host"]} con clave SSH')
        return ssh

    # Sin clave SSH, pedir contraseña por terminal
    warn('No se pudo conectar con clave SSH')

    result = subprocess.run(['which', 'sshpass'], capture_output=True)
    if result.returncode != 0:
        print(f'\n  Opciones:')
        print(f'    1. Añadir SSH_PASSWORD=tu-contraseña en .env (requiere sshpass)')
        print(f'    2. Configurar clave SSH: ssh-copy-id {config["ssh_user"]}@{config["ssh_host"]}')
        print(f'    3. Instalar sshpass: sudo apt install sshpass')
        err('No se puede conectar al servidor')

    password = getpass.getpass(f'Contraseña SSH para {config["ssh_user"]}@{config["ssh_host"]}: ')
    ssh = SSH(
        host=config['ssh_host'],
        user=config['ssh_user'],
        port=int(config['ssh_port']),
        password=password,
    )

    if not ssh.test():
        err('Contraseña incorrecta o servidor inaccesible')

    log(f'Conectado a {config["ssh_host"]} con contraseña')
    return ssh


# ============================================================
# Pasos de instalacion
# ============================================================

def verificar_ubuntu(ssh):
    result = ssh.run_quiet('cat /etc/os-release')
    if 'Ubuntu 24.04' not in result.stdout:
        err('El servidor no es Ubuntu 24.04 LTS')
    log('Ubuntu 24.04 detectado')


def instalar_paquetes(ssh):
    step('Instalando paquetes del sistema')
    ssh.run('apt update -qq')
    ssh.run('DEBIAN_FRONTEND=noninteractive apt install -y -qq python3 python3-venv '
            'python3-pip nginx supervisor certbot python3-certbot-nginx ufw git curl')
    log('Paquetes instalados')


def crear_usuario(ssh, config):
    step('Configurando usuario')
    user = config['user']
    result = ssh.run_quiet(f'id {user}')
    if result.returncode != 0:
        ssh.run(f'useradd -m -s /bin/bash {user}')
        log(f'Usuario {user} creado')
    else:
        log(f'Usuario {user} ya existe')


def desplegar_codigo(ssh, config):
    """Sube el codigo al servidor por repo (git clone) o upload (zip local)."""
    app_dir = config['app_dir']
    user = config['user']

    if config['method'] == 'repo':
        step('Clonando repositorio')
        result = ssh.run_quiet(f'test -d {app_dir}')
        if result.returncode == 0:
            warn(f'{app_dir} ya existe, actualizando...')
            ssh.run(f'su - {user} -c "cd {app_dir} && git pull"')
        else:
            ssh.run(f'su - {user} -c "git clone {config["repo"]} {app_dir}"')
        log(f'Repositorio listo en {app_dir}')

    else:
        step('Subiendo proyecto al servidor')
        proyecto_dir = config['proyecto_dir']
        zip_name = 'server-analytics.tar.gz'
        zip_local = os.path.join('/tmp', zip_name)
        zip_remote = f'/tmp/{zip_name}'

        # Crear tar.gz excluyendo archivos innecesarios
        parent_dir = os.path.dirname(proyecto_dir)
        folder_name = os.path.basename(proyecto_dir)
        excludes = (
            '--exclude=venv --exclude=__pycache__ --exclude=db.sqlite3 '
            '--exclude=.env --exclude=data --exclude=staticfiles --exclude=*.pyc'
        )
        subprocess.run(
            ['tar', 'czf', zip_local] + excludes.split() + ['-C', parent_dir, folder_name],
            check=True,
        )
        log(f'Proyecto comprimido ({os.path.getsize(zip_local) // 1024} KB)')

        # Subir al servidor
        ssh.upload(zip_local, zip_remote)
        log('Archivo subido al servidor')

        # Extraer en el servidor
        ssh.run(f'mkdir -p /home/{user}')
        ssh.run(f'tar xzf {zip_remote} -C /home/{user}')
        # Renombrar al nombre esperado
        nombre_carpeta = os.path.basename(proyecto_dir)
        ssh.run(f'rm -rf "{app_dir}"')
        ssh.run(f'mv "/home/{user}/{nombre_carpeta}" "{app_dir}"')
        ssh.run(f'chown -R {user}:{user} "{app_dir}"')
        log(f'Proyecto desplegado en {app_dir}')

        # Limpiar
        os.remove(zip_local)
        ssh.run(f'rm -f {zip_remote}')


def configurar_python(ssh, config):
    step('Configurando Python')
    venv = config['venv']
    app_dir = config['app_dir']
    user = config['user']

    ssh.run(f'su - {user} -c "python3 -m venv {venv}"')
    ssh.run(f'su - {user} -c "{venv}/bin/pip install -q --upgrade pip"')
    ssh.run(f'su - {user} -c "{venv}/bin/pip install -q -r {app_dir}/requirements.txt"')
    ssh.run(f'su - {user} -c "{venv}/bin/pip install -q gunicorn"')
    log('Dependencias instaladas')


def generar_env(ssh, config):
    step('Generando .env en el servidor')
    app_dir = config['app_dir']
    user = config['user']
    venv = config['venv']

    # Auto-generar SECRET_KEY si esta vacia
    secret_key = config['secret_key']
    if not secret_key:
        result = ssh.run(f'su - {user} -c \'{venv}/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"\'', quiet=True)
        secret_key = result.stdout.strip()
        log('SECRET_KEY generada automaticamente')

    # Auto-generar API_KEY si esta vacia
    api_key = config['api_key']
    if not api_key:
        result = ssh.run('openssl rand -hex 24', quiet=True)
        api_key = result.stdout.strip()
        log('API_KEY generada automaticamente')

    env_content = (
        f'SECRET_KEY={secret_key}\\n'
        f'DEBUG=False\\n'
        f'ALLOWED_HOSTS={config["domain"]}\\n'
        f'API_KEY={api_key}\\n'
        f'TELEGRAM_BOT_TOKEN={config["tg_token"]}\\n'
        f'TELEGRAM_CHAT_ID={config["tg_chat"]}\\n'
        f'SITE_DOMAIN=https://{config["domain"]}\\n'
        f'SITE_AUTHOR={config["author"]}\\n'
        f'SITE_AUTHOR_URL={config["author_url"]}\\n'
        f'WHITELIST_IPS={config["whitelist"]}\\n'
    )

    ssh.run(f'echo -e "{env_content}" > {app_dir}/.env')
    ssh.run(f'chown {user}:{user} {app_dir}/.env')
    ssh.run(f'chmod 600 {app_dir}/.env')
    log('.env generado con permisos 600')


def configurar_django(ssh, config):
    step('Configurando Django')
    app_dir = config['app_dir']
    venv = config['venv']
    user = config['user']
    python = f'{venv}/bin/python'

    ssh.run(f'su - {user} -c "cd {app_dir} && {python} manage.py migrate --noinput"')
    log('Migraciones aplicadas')

    # Crear servidor en la BD (necesario para el daemon analizar_logs)
    domain = config['domain']
    ssh.run(f'su - {user} -c \'cd {app_dir} && {python} manage.py shell -c "from monitor.models import Servidor; Servidor.objects.get_or_create(nombre=\\\"vps-production\\\", defaults={{\\\"ip\\\": \\\"0.0.0.0\\\", \\\"sistema_operativo\\\": \\\"Ubuntu 24.04 LTS\\\"}})"\'')
    log('Servidor creado en la BD')

    ssh.run(f'su - {user} -c "cd {app_dir} && {python} manage.py sync_cards"')
    log('Cards sincronizadas')

    ssh.run(f'su - {user} -c "cd {app_dir} && {python} manage.py collectstatic --noinput"')
    log('Archivos estaticos recopilados')

    # Permisos para que Nginx (www-data) pueda leer los archivos estaticos
    ssh.run(f'chmod 755 /home/{user}')
    ssh.run(f'chmod -R 755 "{app_dir}/staticfiles"')
    log('Permisos de static configurados')


def configurar_ssl_params(ssh):
    step('Configurando SSL')
    result = ssh.run_quiet('test -f /etc/ssl/certs/dhparam.pem')
    if result.returncode != 0:
        warn('Generando DH params (puede tardar unos minutos)...')
        ssh.run('openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048')
        log('DH params generados')
    else:
        log('DH params ya existen')


def _escribir_remoto(ssh, contenido, ruta_remota):
    """Escribe un archivo en el servidor: genera local en /tmp, sube por SCP, elimina local."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(contenido)
        tmp_path = f.name
    ssh.upload(tmp_path, ruta_remota)
    os.remove(tmp_path)


def configurar_nginx(ssh, config):
    step('Configurando Nginx')
    domain = config['domain']
    app_dir = config['app_dir']

    nginx_conf = f"""server {{
    listen 80;
    server_name {domain};
    return 301 https://$host$request_uri;
}}

server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {domain};
    client_max_body_size 60M;
    server_tokens off;

    add_header X-Robots-Tag "index, follow";
    add_header Permissions-Policy "accelerometer=(), camera=(), geolocation=(), microphone=()" always;
    add_header Cross-Origin-Resource-Policy "same-origin" always;

    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/{domain}/chain.pem;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL_SA:50m;
    ssl_session_tickets off;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256:TLS_AES_128_GCM_SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;

    location /static/ {{
        alias {app_dir}/staticfiles/;
    }}

    location / {{
        proxy_pass http://127.0.0.1:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    _escribir_remoto(ssh, nginx_conf, '/etc/nginx/sites-available/serveranalytics')
    ssh.run('rm -f /etc/nginx/sites-enabled/default')
    ssh.run('ln -sf /etc/nginx/sites-available/serveranalytics /etc/nginx/sites-enabled/')
    log('Nginx configurado')


def instalar_ssl(ssh, config):
    domain = config['domain']
    email = config['email']

    temp_conf = f"""server {{
    listen 80;
    server_name {domain};
    location / {{
        return 200 'ok';
    }}
}}
"""
    _escribir_remoto(ssh, temp_conf, '/etc/nginx/sites-available/serveranalytics-temp')
    ssh.run('ln -sf /etc/nginx/sites-available/serveranalytics-temp /etc/nginx/sites-enabled/serveranalytics')
    ssh.run('nginx -t && systemctl reload nginx')

    ssh.run(f'certbot --nginx -d {domain} --non-interactive --agree-tos --email {email} --redirect')
    log('Certificado SSL instalado')

    ssh.run('ln -sf /etc/nginx/sites-available/serveranalytics /etc/nginx/sites-enabled/serveranalytics')
    ssh.run('rm -f /etc/nginx/sites-available/serveranalytics-temp')
    ssh.run('nginx -t && systemctl reload nginx')
    log('Nginx con SSL activo')


def configurar_supervisor(ssh, config):
    step('Configurando Supervisor')
    app_dir = config['app_dir']
    venv = config['venv']
    user = config['user']

    supervisor_conf = f"""[program:serveranalytics]
command={venv}/bin/gunicorn server_analytics.wsgi:application --bind 127.0.0.1:9000 --workers 1
directory={app_dir}
user={user}
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/serveranalytics.log
stderr_logfile=/var/log/supervisor/serveranalytics_err.log
environment=DJANGO_SETTINGS_MODULE="server_analytics.settings"

[program:analizar_logs]
command={venv}/bin/python manage.py analizar_logs --daemon --bloquear
directory={app_dir}
user=root
autostart=true
autorestart=true
stdout_logfile=/var/log/supervisor/analizar_logs.log
stderr_logfile=/var/log/supervisor/analizar_logs_err.log
environment=DJANGO_SETTINGS_MODULE="server_analytics.settings",PYTHONUNBUFFERED="1"
"""

    _escribir_remoto(ssh, supervisor_conf, '/etc/supervisor/conf.d/serveranalytics.conf')
    # Asegurar que el access log existe para el daemon
    ssh.run('touch /var/log/nginx/access.log')
    ssh.run('supervisorctl reread')
    ssh.run('supervisorctl update')
    ssh.run('supervisorctl restart serveranalytics')
    log('Gunicorn iniciado')
    result = ssh.run('supervisorctl restart analizar_logs', check=False)
    if result.returncode == 0:
        log('Daemon analizar_logs iniciado')
    else:
        warn('analizar_logs no arranco (se reintentara automaticamente)')


def configurar_firewall(ssh):
    step('Configurando firewall')
    ssh.run('ufw allow OpenSSH')
    ssh.run("ufw allow 'Nginx Full'")
    ssh.run('echo y | ufw enable')
    log('UFW activo (SSH + Nginx)')


def mostrar_resumen(config):
    domain = config['domain']
    print(f'\n{GREEN}============================================{NC}')
    print(f'{GREEN}  Server Analytics instalado correctamente  {NC}')
    print(f'{GREEN}============================================{NC}')
    print(f'')
    print(f'  URL:        {CYAN}https://{domain}{NC}')
    print(f'  Servidor:   {config["ssh_host"]}')
    print(f'  Directorio: {config["app_dir"]}')
    print(f'  Usuario:    {config["user"]}')
    print(f'  Logs:       /var/log/supervisor/')
    print(f'')
    print(f'  Comandos utiles:')
    print(f'    ssh {config["ssh_user"]}@{config["ssh_host"]} "supervisorctl status"')
    print(f'    ssh {config["ssh_user"]}@{config["ssh_host"]} "supervisorctl restart all"')
    print(f'')


# ============================================================
# Main
# ============================================================

def main():
    config = cargar_configuracion()
    ssh = conectar(config)

    verificar_ubuntu(ssh)
    instalar_paquetes(ssh)
    crear_usuario(ssh, config)
    desplegar_codigo(ssh, config)
    configurar_python(ssh, config)
    generar_env(ssh, config)
    configurar_django(ssh, config)
    configurar_ssl_params(ssh)
    configurar_nginx(ssh, config)
    instalar_ssl(ssh, config)
    configurar_supervisor(ssh, config)
    configurar_firewall(ssh)
    mostrar_resumen(config)


if __name__ == '__main__':
    main()
