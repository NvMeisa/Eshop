"""
Система аутентификации для API
"""

from datetime import datetime, timedelta
from typing import Optional

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.authentication import (
    BaseAuthentication,
    SessionAuthentication,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

User = get_user_model()


class JWTAuthentication(BaseAuthentication):
    """
    JWT аутентификация для API
    """

    def authenticate(self, request):
        """Аутентификация по JWT токену"""
        auth_header = request.META.get('HTTP_AUTHORIZATION')

        if not auth_header:
            return None

        try:
            # Извлекаем токен из заголовка
            token = auth_header.split(' ')[1]
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=['HS256']
            )

            user_id = payload.get('user_id')
            if user_id is None:
                return None

            user = User.objects.get(id=user_id)
            return (user, token)

        except (jwt.InvalidTokenError, User.DoesNotExist, IndexError):
            return None

    def authenticate_header(self, request):
        """Заголовок для аутентификации"""
        return 'Bearer'


class APIKeyAuthentication(BaseAuthentication):
    """
    Аутентификация по API ключу
    """

    def authenticate(self, request):
        """Аутентификация по API ключу"""
        api_key = request.META.get('HTTP_X_API_KEY')

        if not api_key:
            return None

        # Здесь должна быть проверка API ключа
        # В реальном проекте используйте модель для хранения ключей
        if api_key == getattr(settings, 'API_KEY', None):
            # Возвращаем анонимного пользователя для API ключей
            return (None, api_key)

        return None

    def authenticate_header(self, request):
        """Заголовок для аутентификации"""
        return 'X-API-Key'


class HybridAuthentication(BaseAuthentication):
    """
    Гибридная аутентификация (JWT + API Key)
    """

    def __init__(self):
        self.jwt_auth = JWTAuthentication()
        self.api_key_auth = APIKeyAuthentication()

    def authenticate(self, request):
        """Попытка аутентификации разными методами"""
        # Сначала пробуем JWT
        jwt_result = self.jwt_auth.authenticate(request)
        if jwt_result:
            return jwt_result

        # Затем API ключ
        api_key_result = self.api_key_auth.authenticate(request)
        if api_key_result:
            return api_key_result

        return None

    def authenticate_header(self, request):
        """Заголовок для аутентификации"""
        return 'Bearer, X-API-Key'


class TokenManager:
    """
    Менеджер токенов для API
    """

    @staticmethod
    def generate_token(user: User, expires_in: int = 3600) -> str:
        """Генерация JWT токена"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
        }

        return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    @staticmethod
    def decode_token(token: str) -> Optional[dict]:
        """Декодирование JWT токена"""
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except jwt.InvalidTokenError:
            return None

    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Проверка истечения токена"""
        payload = TokenManager.decode_token(token)
        if not payload:
            return True

        exp = payload.get('exp')
        if not exp:
            return True

        return datetime.utcnow() > datetime.fromtimestamp(exp)


class AuthenticationMixin:
    """
    Миксин для добавления аутентификации к ViewSet
    """

    def get_authentication_classes(self):
        """Получение классов аутентификации"""
        if hasattr(self, 'authentication_classes'):
            return self.authentication_classes

        # По умолчанию используем гибридную аутентификацию
        return [HybridAuthentication, SessionAuthentication]

    def get_permission_classes(self):
        """Получение классов разрешений"""
        if hasattr(self, 'permission_classes'):
            return self.permission_classes

        # По умолчанию требуем аутентификацию
        return [IsAuthenticated]


def require_auth(view_func):
    """
    Декоратор для требования аутентификации
    """

    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response(
                {'error': 'Authentication required'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        return view_func(request, *args, **kwargs)

    return wrapper


def optional_auth(view_func):
    """
    Декоратор для опциональной аутентификации
    """

    def wrapper(request, *args, **kwargs):
        # Аутентификация необязательна
        return view_func(request, *args, **kwargs)

    return wrapper
