"""
Middleware de rate limiting por IP.

Limita las peticiones por IP usando una ventana deslizante en memoria.
Configuracion en settings.py:
    RATE_LIMIT_REQUESTS: maximo de peticiones por ventana (default: 60)
    RATE_LIMIT_WINDOW: duracion de la ventana en segundos (default: 60)

Usa la cabecera X-Real-IP que nginx configura con $remote_addr,
que no es manipulable por el cliente (a diferencia de X-Forwarded-For).
"""
import time
from django.http import JsonResponse
from django.conf import settings

MAX_TRACKED_IPS = 10000


class RateLimitMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        self.requests = {}
        self.max_requests = getattr(settings, 'RATE_LIMIT_REQUESTS', 60)
        self.window = getattr(settings, 'RATE_LIMIT_WINDOW', 60)
        self.last_cleanup = time.time()

    def __call__(self, request):
        ip = self._get_ip(request)
        now = time.time()

        if now - self.last_cleanup > self.window * 2:
            self._cleanup(now)

        if ip not in self.requests:
            self.requests[ip] = []

        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window]

        if len(self.requests[ip]) >= self.max_requests:
            return JsonResponse(
                {'error': 'Demasiadas peticiones. Espera un momento.'},
                status=429,
            )

        self.requests[ip].append(now)
        return self.get_response(request)

    def _cleanup(self, now):
        """Elimina IPs expiradas y recorta el diccionario si supera el limite."""
        expired = [ip for ip, ts in self.requests.items() if not ts or now - ts[-1] > self.window]
        for ip in expired:
            del self.requests[ip]
        if len(self.requests) > MAX_TRACKED_IPS:
            sorted_ips = sorted(self.requests.items(), key=lambda x: x[1][-1] if x[1] else 0)
            for ip, _ in sorted_ips[:len(self.requests) - MAX_TRACKED_IPS]:
                del self.requests[ip]
        self.last_cleanup = now

    def _get_ip(self, request):
        """Obtiene la IP real del cliente desde la cabecera X-Real-IP de nginx."""
        real_ip = request.META.get('HTTP_X_REAL_IP')
        if real_ip:
            return real_ip.strip()
        return request.META.get('REMOTE_ADDR', '')
