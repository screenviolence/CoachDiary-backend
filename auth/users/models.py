from django.contrib.auth.models import (AbstractBaseUser, BaseUserManager,
                                        PermissionsMixin)
from django.db import models


class LowerCaseEmailField(models.EmailField):
    """Custom email field to provide case insensitive email."""

    def get_prep_value(self, value):
        email = super().get_prep_value(value)

        if email is not None:
            email = email.lower()

        return email


class UserManager(BaseUserManager):
    """Custom user manager which provides correct creation of superuser."""

    def build_user(self, email: str, password: str, name: str) -> "User":
        if email is None:
            raise TypeError("Users must have an email address.")

        if password is None:
            raise TypeError("Users must have a password")

        if name is None:
            raise TypeError("Users must have a name")

        user = self.model(email=self.normalize_email(email))
        user.set_password(password)

        return user

    def create_user(self, email: str, password: str, name: str) -> "User":
        user = self.build_user(email, password, name)
        user.save()
        return user

    def create_superuser(self, email: str, password: str, name: str) -> "User":
        if password is None:
            raise TypeError('Superusers must have a password.')

        user = self.build_user(email, password, name)
        user.is_superuser = True
        user.is_staff = True
        user.save()

        return user


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model.

    It is used to provide login via email instead of username as username will
    not be used.

    """
    name = models.CharField(max_length=255)
    email = LowerCaseEmailField(
        blank=False,
        unique=True,
    )
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = "email"

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
