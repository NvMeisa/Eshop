"""
Конфигурация для API приложения
"""

# Настройки пагинации
API_PAGINATION = {
    'DEFAULT_PAGE_SIZE': 20,
    'MAX_PAGE_SIZE': 100,
    'PAGE_SIZE_QUERY_PARAM': 'page_size',
}

# Настройки версионирования
API_VERSIONING = {
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1', 'v2'],
    'VERSION_PARAM': 'version',
}

# Настройки аутентификации
API_AUTHENTICATION = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# Настройки фильтрации
API_FILTERS = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'SEARCH_PARAM': 'search',
    'ORDERING_PARAM': 'ordering',
}

# Настройки кэширования
API_CACHE = {
    'DEFAULT_CACHE_TIMEOUT': 300,  # 5 минут
    'CACHE_KEY_PREFIX': 'api',
}

# Настройки мониторинга
API_MONITORING = {
    'ENABLE_LOGGING': True,
    'LOG_LEVEL': 'INFO',
    'ENABLE_METRICS': True,
}

# Настройки документации
API_DOCS = {
    'TITLE': 'Eshop API',
    'DESCRIPTION': 'API для интернет-магазина Eshop',
    'VERSION': '1.0.0',
    'CONTACT': {
        'name': 'API Support',
        'email': 'support@eshop.com',
    },
    'LICENSE': {
        'name': 'MIT',
        'url': 'https://opensource.org/licenses/MIT',
    },
}

# Настройки ограничений
API_THROTTLING = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
    },
}

# Настройки CORS
API_CORS = {
    'ALLOWED_ORIGINS': [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
    ],
    'ALLOWED_METHODS': [
        'GET',
        'POST',
        'PUT',
        'PATCH',
        'DELETE',
        'OPTIONS',
    ],
    'ALLOWED_HEADERS': [
        'accept',
        'accept-encoding',
        'authorization',
        'content-type',
        'dnt',
        'origin',
        'user-agent',
        'x-csrftoken',
        'x-requested-with',
    ],
}
