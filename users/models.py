from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models

from common.models import HumanModel


class LowerCaseEmailField(models.EmailField):
    """Custom email field to provide case insensitive email."""

    def get_prep_value(self, value):
        email = super().get_prep_value(value)

        if email is not None:
            email = email.lower()

        return email


class UserManager(BaseUserManager):
    """Custom user manager which provides the correct creation of superuser."""

    def build_user(self, email: str, password: str, first_name: str, last_name: str, patronymic: str = None,
                   role: str = None) -> "User":
        if email is None:
            raise TypeError("Нужно указать эл. почту")

        if password is None:
            raise TypeError("Нужно указать пароль")

        if first_name is None:
            raise TypeError("Нужно указать имя")

        if last_name is None:
            raise TypeError("Нужно указать фамилию")

        user = self.model(email=self.normalize_email(email), first_name=first_name, last_name=last_name)

        if patronymic:
            user.patronymic = patronymic

        if role:
            user.role = role

        user.set_password(password)

        return user

    def create_user(self, email: str, password: str, first_name: str, last_name: str, patronymic: str = None,
                    role: str = None) -> "User":
        user = self.build_user(email, password, first_name, last_name, patronymic, role)
        user.save()
        return user

    def create_superuser(self, email: str, password: str, first_name: str, last_name: str,
                         patronymic: str = None) -> "User":

        if password is None:
            raise TypeError('У администратора должен быть пароль.')

        user = self.build_user(email, password, first_name, last_name, patronymic)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


class User(AbstractBaseUser, HumanModel, PermissionsMixin):
    """Custom user model.

    It is used to provide login via email instead of username as username will
    not be used.

    """
    ROLE_CHOICES = (
        ('teacher', 'Тренер'),
        ('student', 'Учащийся'),
    )

    email = LowerCaseEmailField(blank=False, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='teacher')
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, null=True, blank=True)
    password_reset_token = models.UUIDField(null=True, blank=True)
    password_reset_expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.full_name

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
