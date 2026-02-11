from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'escalas', EscalaViewSet)
router.register(r'musicos', MusicoViewSet)
router.register(r'eventos', EventoViewSet)
router.register(r'musicas', MusicaViewSet)
router.register(r'repertorio', EscalaRepertorioViewSet)



urlpatterns = [
    path('', include(router.urls)),
]