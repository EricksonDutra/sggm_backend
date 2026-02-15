from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from core.admin import admin_site
from core.api.views import (
    EscalaViewSet,
    EventoViewSet,
    InstrumentoViewSet,
    MusicaViewSet,
    MusicoViewSet,
    MyTokenObtainPairView,
)

router = DefaultRouter()
router.register(r"eventos", EventoViewSet)
router.register(r"musicos", MusicoViewSet)
router.register(r"escalas", EscalaViewSet)
router.register(r"musicas", MusicaViewSet)
router.register(r"instrumentos", InstrumentoViewSet)

urlpatterns = [
    path("admin/", admin_site.urls),
    path("api/", include(router.urls)),
    path("api/login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
