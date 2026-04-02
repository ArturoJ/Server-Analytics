"""Tests del middleware de rate limiting."""
from django.test import TestCase, RequestFactory

from monitor.middleware import RateLimitMiddleware


class RateLimitTest(TestCase):

    def test_peticiones_normales_pasan(self):
        """Peticiones dentro del limite pasan sin problema."""
        for _ in range(5):
            resp = self.client.get('/api/dashboard/')
            self.assertEqual(resp.status_code, 200)

    def test_rate_limit_bloquea(self):
        """Superar el limite devuelve 429."""
        middleware = RateLimitMiddleware(lambda r: None)
        middleware.max_requests = 3
        middleware.window = 60

        factory = RequestFactory()
        for i in range(5):
            request = factory.get('/api/dashboard/')
            request.META['REMOTE_ADDR'] = '10.10.10.10'
            resp = middleware(request)
            if resp and hasattr(resp, 'status_code') and resp.status_code == 429:
                self.assertGreaterEqual(i, 3)
                return
        self.fail('El rate limit no se activo')
