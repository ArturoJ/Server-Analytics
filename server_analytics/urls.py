from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # path('gestion-x7k9m2p4/', admin.site.urls),
    path('', include('monitor.urls')),
]
