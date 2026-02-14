from django.urls import include, path
from rest_framework.routers import DefaultRouter

from ..views import logout_view
from .views import (
    EscalaViewSet,
    EventoViewSet,
    InstrumentoViewSet,
    MusicaViewSet,
    MusicoViewSet,
)

router = DefaultRouter()
router.register(r"musicos", MusicoViewSet)
router.register(r"musicas", MusicaViewSet)
router.register(r"eventos", EventoViewSet)
router.register(r"escalas", EscalaViewSet)
router.register(r"instrumentos", InstrumentoViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("logout/", logout_view, name="logout"),
]
