from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
import datetime
import logging

from common.models import (
    BaseModel,
    GenderChoices,
)
from standards.models import Level, Standard
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
    def recruitment_year(self):
        """Вычисляет год набора класса"""
        current_year = timezone.now().year
        return current_year - self.number

    def clean(self):
        if self.recruitment_year > datetime.date.today().year:
            raise ValidationError(
                "Год набора не может быть позднее текущего года.",
            )

    def __str__(self):
        return f"{self.number}{self.class_name}"

    class Meta:
        verbose_name = "Класс"
        verbose_name_plural = "Классы"
        ordering = ['number', 'class_name']
        unique_together = ['number', 'class_name']


class Student(BaseModel):
    """
    Модель ученика.
    """
    full_name = models.CharField(
        max_length=255,
        verbose_name="Полное имя ученика",
        help_text="Петров Петр Петрович",
    )
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
    # Возможность связать ученика с пользователем системы
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
        ordering = ['student_class', 'full_name']


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


class StudentStandard(BaseModel):
    """
    Результаты выполнения нормативов учениками.
    """
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="standards",
        verbose_name="Ученик",
    )
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name="results",
        verbose_name="Норматив",
    )
    grade = models.IntegerField(
        verbose_name="Оценка",
        validators=[MinValueValidator(2), MaxValueValidator(5)]
    )
    value = models.FloatField(
        verbose_name="Значение",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        verbose_name="Уровень",
        null=True,
        blank=True,
    )
    date_recorded = models.DateField(
        default=timezone.now,
        verbose_name="Дата записи"
    )
    teacher = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Учитель, записавший результат",
        limit_choices_to={'role__in': ['teacher', 'admin']},
    )

    def save(self, *args, **kwargs):
        # Округляем оценку до целого, если это дробное число
        if isinstance(self.grade, float):
            self.grade = round(self.grade)

        # Получаем класс ученика
        student_class_number = self.student.student_class.number

        # Пытаемся найти соответствующий уровень
        try:
            self.level = Level.objects.get(
                standard=self.standard,
                level_number=student_class_number,
                gender=self.student.gender,
            )
        except Level.DoesNotExist:
            logging.warning(
                f"Уровень для норматива '{self.standard.name}', класса {student_class_number} "
                f"и пола '{self.student.get_gender_display()}' не найден."
            )
            self.level = None
        except Exception as e:
            logging.error(f"Непредвиденная ошибка при сохранении результата: {e}")
            self.level = None

        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.student.full_name} - {self.standard.name}: "
            f"{self.value} ({self.grade})"
        )

    class Meta:
        verbose_name = "Результат ученика"
        verbose_name_plural = "Результаты учеников"
        ordering = ['-date_recorded', 'student']
