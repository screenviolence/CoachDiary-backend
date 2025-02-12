import os

from invoke.tasks import task

# Project commands


@task
def install_requirements(context):
    context.run("poetry install")


# Django commands

def manage(context, command):
    context.run(f"python manage.py {command}")


@task
def run(context):
    manage(context, "runserver")


@task
def makemigrations(context):
    manage(context, "makemigrations")


@task
def migrate(context):
    manage(context, "migrate")


@task
def django_shell(context):
    manage(context, "shell_plus")


@task
def create_superuser(
    context,
    email: str = "root@root.com",
    password: str = "root",
):
    os.environ.setdefault("DJANGO_SUPERUSER_EMAIL", email)
    os.environ.setdefault("DJANGO_SUPERUSER_PASSWORD", password)

    manage(context, "createsuperuser --noinput")
