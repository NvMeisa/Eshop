"""
Главные URL маршруты для API
"""

from django.http import JsonResponse
from django.urls import include, path
from django.views.generic import View
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

# Импортируем URL для разных версий API
from .v1 import urls as v1_urls

# Определяем namespace для API
app_name = 'api'


class APIInfoView(View):
    """Информационная страница API"""

    def get(self, request):
        return JsonResponse(
            {
                'message': 'Eshop API',
                'version': '1.0',
                'available_versions': {
                    'v1': '/api/v1/',
                    'docs': '/api/docs/',
                    'schema': '/api/schema/',
                    'redoc': '/api/redoc/',
                },
                'description': 'API для интернет-магазина Eshop',
            }
        )


# Главные URL маршруты для API
urlpatterns = [
    # Корневой URL API
    path('', APIInfoView.as_view(), name='api-info'),
    # API версии 1
    path('v1/', include(v1_urls)),
    # Автоматическая документация API
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path(
        'docs/',
        SpectacularSwaggerView.as_view(url_name='api:schema'),
        name='swagger-ui',
    ),
    path(
        'redoc/',
        SpectacularRedocView.as_view(url_name='api:schema'),
        name='redoc',
    ),
    # Аутентификация DRF (только на главном уровне API)
    path('auth/', include('rest_framework.urls')),
    # Здесь можно добавить другие версии API
    # path('v2/', include('api.v2.urls')),
]
