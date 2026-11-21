from django.core.management.base import BaseCommand

from core.sidebar import refresh_sidebar


class Command(BaseCommand):
    help = 'Пересчитывает популярные теги и лучших участников за неделю.'

    def handle(self, *args, **options):
        refresh_sidebar()
        self.stdout.write(self.style.SUCCESS('Боковая колонка обновлена.'))
