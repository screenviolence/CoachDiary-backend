from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError

from django.utils import timezone
import datetime
from common.models import (
    BaseModel,
    GenderChoices, HumanModel,
)
from users.models import User


class StudentClass(BaseModel):
    """
    Модель для учебного класса.
    """
    number = models.IntegerField(
        verbose_name="Номер учебного класса",
        validators=[
            MinValueValidator(1),
            MaxValueValidator(11),
        ],
    )
    class_name = models.CharField(
        max_length=1,
        verbose_name="Буква учебного класса",
        help_text="А, Б, В, ..."
    )
    class_owner = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Куратор класса",
        limit_choices_to={'role__in': ['teacher', 'admin']},
    )
    is_archived = models.BooleanField(
        default=False,
        verbose_name="Архивный класс",
    )

    @property
    def recruitment_year(self) -> int:
        """Вычисляет год набора класса"""
        current_year = timezone.now().year
        return current_year - self.number

    def clean(self):
        if self.recruitment_year > datetime.date.today().year:
            raise ValidationError(
                "Год набора не может быть позднее текущего года.",
            )

    def save(self, *args, **kwargs):
        self.class_name = self.class_name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.number}{self.class_name}"

    class Meta:
        verbose_name = "Класс"
        verbose_name_plural = "Классы"
        ordering = ['number', 'class_name']


class Student(HumanModel):
    """
    Модель ученика.
    """
    student_class = models.ForeignKey(
        StudentClass,
        on_delete=models.CASCADE,
        verbose_name="Класс ученика",
        related_name='students',
    )
    birthday = models.DateField(
        verbose_name="Дата рождения ученика",
    )
    gender = models.CharField(
        max_length=1,
        choices=GenderChoices,
        verbose_name="Пол ученика",
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Учетная запись ученика",
    )

    def __str__(self):
        return f"Ученик {self.full_name} ({self.birthday.strftime('%d.%m.%Y')} г.р.), {self.student_class}"

    class Meta:
        verbose_name = "Ученик"
        verbose_name_plural = "Ученики"
        ordering = ['student_class']


class Invitation(BaseModel):
    """
    Приглашение для ученика.
    """
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name='invitation',
        verbose_name="Ученик"
    )
    invite_code = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Код приглашения"
    )
    is_used = models.BooleanField(
        default=False,
        verbose_name="Использовано"
    )

    def get_join_link(self):
        return f"https://coachdiary.ru/join/{self.invite_code}"

    def __str__(self):
        return f"Приглашение для {self.student.full_name}: {self.invite_code}"

    class Meta:
        verbose_name = "Приглашение"
        verbose_name_plural = "Приглашения"
