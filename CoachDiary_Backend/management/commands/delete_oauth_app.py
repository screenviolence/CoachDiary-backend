from django.core.management.base import BaseCommand
from oauth2_provider.models import Application
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Delete OAuth2 applications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            dest='app_id',
            help='ID удаляемого приложения',
        )
        parser.add_argument(
            '--client-id',
            dest='client_id',
            help='Client ID удаляемого приложения',
        )
        parser.add_argument(
            '--email',
            dest='email',
            help='Удалить все приложения, принадлежащие пользователю с заданной эл. почтой',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Удалить все приложения (ОСТОРОЖНО!)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Удалить без подтверждения',
        )

    def handle(self, *args, **options):
        app_id = options.get('app_id')
        client_id = options.get('client_id')
        email = options.get('email')
        delete_all = options.get('all', False)
        force = options.get('force', False)

        applications = Application.objects.all()

        if app_id:
            applications = applications.filter(id=app_id)
        elif client_id:
            applications = applications.filter(client_id=client_id)
        elif email:
            try:
                user = User.objects.get(email=email)
                applications = applications.filter(user=user)
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Пользователь с email '{email}' не найден"))
                return
        elif not delete_all:
            self.stdout.write(self.style.ERROR("Необходимо указать --id, --client-id, --email или --all"))
            return

        count = applications.count()
        if count == 0:
            self.stdout.write(self.style.WARNING("Не найдено приложений для удаления"))
            return

        if not force:
            confirm = input(f"Вы уверены, что хотите удалить {count} приложений? [y/N]: ")
            if confirm.lower() != 'y':
                self.stdout.write(self.style.WARNING("Операция отменена"))
                return

        self.stdout.write(self.style.WARNING("Следующие приложения будут удалены:"))
        for app in applications:
            self.stdout.write(f"ID: {app.id}, Название: {app.name}, Client ID: {app.client_id}")

        applications.delete()
        self.stdout.write(self.style.SUCCESS(f"Успешно удалено {count} приложений"))
