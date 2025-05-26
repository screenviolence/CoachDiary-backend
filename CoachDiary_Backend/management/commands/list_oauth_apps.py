from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from oauth2_provider.models import Application

User = get_user_model()


class Command(BaseCommand):
    help = 'Список всех OAuth приложений'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            dest='email',
            help='Фильтр приложений по эл. почте администратора',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Вывод подробной информации о приложении',
        )

    def handle(self, *args, **options):
        email = options.get('email')
        verbose = options.get('verbose', False)

        applications = Application.objects.all().order_by('name')

        if email:
            try:
                user = User.objects.get(email=email)
                applications = applications.filter(user=user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Пользователь с email '{email}' не найден"))
                return

        if not applications.exists():
            self.stdout.write(self.style.WARNING("Не найдено ни одного OAuth приложения"))
            return

        self.stdout.write(self.style.SUCCESS(f"Найдено {applications.count()} OAuth приложений:"))
        self.stdout.write("-" * 80)

        for app in applications:
            self.stdout.write(f"ID: {app.id}, Название: {app.name}, Client ID: {app.client_id}")

            if verbose:
                self.stdout.write(f"  Пользователь: {app.user.email if app.user else 'Нет'}")
                self.stdout.write(f"  Тип клиента: {app.client_type}")
                self.stdout.write(f"  Тип авторизации: {app.authorization_grant_type}")
                self.stdout.write(f"  Редирект URIs: {app.redirect_uris}")
                self.stdout.write(f"  Дата создания: {app.created}")
                self.stdout.write(f"  Дата обновления: {app.updated}")

            self.stdout.write("-" * 80)
