"""
Команда для оптимизации базы данных
"""
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.db import connection
from main.models import Cart, CartItem, Category, Product


class Command(BaseCommand):
    help = 'Оптимизация базы данных и кэша'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Очистить весь кэш',
        )
        parser.add_argument(
            '--analyze-tables',
            action='store_true',
            help='Анализировать таблицы для оптимизации',
        )
        parser.add_argument(
            '--vacuum',
            action='store_true',
            help='Выполнить VACUUM для SQLite',
        )

    def handle(self, *args, **options):
        self.stdout.write('🚀 Начинаем оптимизацию...')

        if options['clear_cache']:
            self.clear_cache()

        if options['analyze_tables']:
            self.analyze_tables()

        if options['vacuum']:
            self.vacuum_database()

        self.stdout.write('✅ Оптимизация завершена!')

    def clear_cache(self):
        """Очистка всего кэша"""
        self.stdout.write('🧹 Очищаем кэш...')
        cache.clear()
        self.stdout.write('✅ Кэш очищен')

    def analyze_tables(self):
        """Анализ таблиц для оптимизации"""
        self.stdout.write('📊 Анализируем таблицы...')
        
        with connection.cursor() as cursor:
            # Анализируем размеры таблиц
            cursor.execute("""
                SELECT name, sql FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
            """)
            
            tables = cursor.fetchall()
            
            for table_name, table_sql in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                
                self.stdout.write(f'📋 Таблица {table_name}: {count} записей')
                
                # Анализируем индексы
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                
                if indexes:
                    self.stdout.write(f'   🔍 Индексы: {len(indexes)}')
                else:
                    self.stdout.write(f'   ⚠️  Индексы отсутствуют')

    def vacuum_database(self):
        """Выполнение VACUUM для SQLite"""
        self.stdout.write('🧹 Выполняем VACUUM...')
        
        with connection.cursor() as cursor:
            cursor.execute("VACUUM")
        
        self.stdout.write('✅ VACUUM выполнен')

    def get_database_stats(self):
        """Получение статистики базы данных"""
        stats = {
            'products': Product.objects.count(),
            'categories': Category.objects.count(),
            'carts': Cart.objects.count(),
            'cart_items': CartItem.objects.count(),
        }
        
        self.stdout.write('📈 Статистика базы данных:')
        for key, value in stats.items():
            self.stdout.write(f'   {key}: {value}')
        
        return stats
