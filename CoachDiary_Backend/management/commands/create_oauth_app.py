from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from oauth2_provider.models import Application

User = get_user_model()


class Command(BaseCommand):
    help = 'Создает OAuth2 приложение'

    def add_arguments(self, parser):
        parser.add_argument(
            '--name',
            default='Мобильное приложение React Native',
            help='Название OAuth2 приложения'
        )
        parser.add_argument(
            '--email',
            help='Эл. почта владельца приложения (по умолчанию - первый суперпользователь)'
        )

    def handle(self, *args, **options):
        app_name = options['name']
        email = options['email']

        try:
            existing_app = Application.objects.filter(name=app_name).first()
            if existing_app:
                self.stdout.write(self.style.WARNING(f'Приложение "{app_name}" уже существует!'))
                self.stdout.write(f'Client ID: {existing_app.client_id}')
                return

            user = None
            if email:
                try:
                    user = User.objects.get(email=email)
                except User.DoesNotExist:
                    raise CommandError(f'Пользователь "{email}" не существует!')
            else:
                user = User.objects.filter(is_superuser=True).first()
                if not user:
                    raise CommandError(
                        'Суперпользователь не найден. Сначала создайте суперпользователя с помощью createsuperuser.')

            app = Application.objects.create(
                name=app_name,
                client_type=Application.CLIENT_PUBLIC,
                authorization_grant_type=Application.GRANT_PASSWORD,
                user=user,
                redirect_uris=''  # Для GRANT_PASSWORD не используется
            )

            self.stdout.write(self.style.SUCCESS(f'OAuth2 приложение "{app_name}" успешно создано!'))
            self.stdout.write(f'Client ID: {app.client_id}')
            self.stdout.write(f'Владелец: {app.user.email}')

        except Exception as e:
            raise CommandError(f'Произошла ошибка при создании OAuth2 приложения: {e}')
