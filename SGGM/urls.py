from django.urls import include, path
from rest_framework_simplejwt.views import TokenRefreshView

from core.admin import admin_site
from core.api.views import MyTokenObtainPairView

urlpatterns = [
    path("admin/", admin_site.urls),
    path("api/", include("core.api.urls")),
    path("api/login/", MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
