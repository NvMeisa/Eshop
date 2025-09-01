"""
Система версионирования API
"""
from django.conf import settings
from rest_framework.settings import api_settings
from rest_framework.versioning import URLPathVersioning


class APIVersioning(URLPathVersioning):
    """
    Кастомная система версионирования API
    """
    default_version = 'v1'
    allowed_versions = ['v1', 'v2']
    version_param = 'version'
    
    def get_default_version(self, request):
        """Получение версии по умолчанию"""
        return self.default_version
    
    def is_allowed_version(self, version):
        """Проверка разрешенной версии"""
        return version in self.allowed_versions
    
    def get_version_param(self):
        """Получение параметра версии"""
        return self.version_param


class VersionedViewSetMixin:
    """
    Миксин для ViewSet с поддержкой версионирования
    """
    
    def get_serializer_class(self):
        """Выбор сериализатора в зависимости от версии"""
        version = self.request.version
        
        if version == 'v2' and hasattr(self, 'serializer_class_v2'):
            return self.serializer_class_v2
        
        return super().get_serializer_class()
    
    def get_queryset(self):
        """Выбор queryset в зависимости от версии"""
        version = self.request.version
        
        if version == 'v2' and hasattr(self, 'queryset_v2'):
            return self.queryset_v2
        
        return super().get_queryset()
    
    def get_permissions(self):
        """Выбор разрешений в зависимости от версии"""
        version = self.request.version
        
        if version == 'v2' and hasattr(self, 'permission_classes_v2'):
            return [permission() for permission in self.permission_classes_v2]
        
        return super().get_permissions()


def get_api_version(request):
    """Получение версии API из запроса"""
    versioning = APIVersioning()
    return versioning.get_version_param(request)


def is_api_version_supported(version):
    """Проверка поддержки версии API"""
    versioning = APIVersioning()
    return versioning.is_allowed_version(version)
