import datetime
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from .base import BaseModel


class StudentClass(BaseModel):
    number = models.IntegerField(
        verbose_name="Номер учебного класса",
        validators=(
            MinValueValidator(1),
            MaxValueValidator(11),
        ),
    )
    class_name = models.CharField(
        max_length=1,
        verbose_name="Буква учебного класса",
        help_text="А, Б, В, ..."
    )
    class_owner = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        verbose_name="Куратор класса",
    )

    @property
    def recruitment_year(self):
        current_year = timezone.now().year
        return current_year - self.number

    def clean(self):
        if self.recruitment_year > datetime.date.today().year:
            raise ValidationError(
                "Год набора не может быть позднее текущего года.",
            )

    def __str__(self) -> str:
        return f"{self.number}{self.class_name}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.recruitment_date = self.recruitment_year
        super().save(*args, **kwargs)


class Student(BaseModel):
    full_name = models.CharField(
        max_length=1024,
        verbose_name="Полное имя ученика",
        help_text="Петров Петр Петрович",
    )
    student_class = models.ForeignKey(
        StudentClass,
        on_delete=models.CASCADE,
        verbose_name="Класс ученика",
    )
    birthday = models.DateField(
        verbose_name="Дата рождения ученика",
    )

    class Gender(models.TextChoices):
        male = "m", "Мужской"
        female = "f", "Женский"

    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        verbose_name="Пол ученика",
    )

    def __str__(self) -> str:
        return (
            f"Ученик {self.full_name} ({self.birthday} г.р.), "
            f"{self.student_class}"
        )


# class StandardValue(BaseModel):
#     standard = models.ForeignKey(
#         to=Standard,
#         on_delete=models.CASCADE,
#         verbose_name="Норматив",
#     )
#     student_class = models.ForeignKey(
#         StudentClass,
#         on_delete=models.CASCADE,
#         verbose_name="Класс",
#     )
#
#     def __str__(self) -> str:
#         return (
#             f"Норматив: {self.standard}, "
#             f"Класс: {self.student_class}, "
#         )


class Standard(models.Model):
    name = models.CharField(
        max_length=255,
        verbose_name="Название норматива",
    )
    who_added = models.ForeignKey(
        "users.User",
        on_delete=models.PROTECT,
        verbose_name="Кто добавил норматив",
    )
    has_numeric_value = models.BooleanField(
        verbose_name="Является ли это умением или нормативом",
        help_text="Если True, то это умение. Иначе - норматив",
    )

    def __str__(self) -> str:
        return self.name

    def get_levels(self):
        return self.levels.all()


class Level(models.Model):
    level_number = models.IntegerField(
        validators=(
            MinValueValidator(1),
        ),
        verbose_name="Номер уровня норматива",
    )
    low_level_value = models.FloatField(
        validators=(
            MinValueValidator(0),
        ),
        verbose_name="Минимальное значение для уровня",
        null=True, blank=True
    )
    middle_level_value = models.FloatField(
        validators=(
            MinValueValidator(0),
        ),
        verbose_name="Среднее значение для уровня",
        null=True, blank=True
    )
    high_level_value = models.FloatField(
        validators=(
            MinValueValidator(0),
        ),
        verbose_name="Лучшее значение для уровня",
        null=True, blank=True
    )
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name="levels",
        verbose_name="Норматив, к которому относится данный уровень",
    )

    class Gender(models.TextChoices):
        male = "m", "Мужской"
        female = "f", "Женский"

    gender = models.CharField(
        max_length=1,
        choices=Gender.choices,
        verbose_name="Пол учеников, для которого рассчитан данный уровень",
    )

    def clean(self):
        if self.standard.has_numeric_value:
            if not all([self.low_level_value, self.middle_level_value, self.high_level_value]):
                raise ValidationError(
                    "Для нормативов с числовым значением необходимо указывать уровневые значения."
                )
        else:
            if any([self.low_level_value, self.middle_level_value, self.high_level_value]):
                raise ValidationError(
                    "Для нормативов без числового значения необходимо указать все уровневые значения."
                )

    def save(self, *args, **kwargs):
        self.clean()  # Ensure the clean method is called
        super().save(*args, **kwargs)


# class StudentStandard(BaseModel):
#     student = models.ForeignKey(
#         Student,
#         on_delete=models.CASCADE,
#         verbose_name="Ученик",
#     )
#     standard = models.ForeignKey(
#         Standard,
#         on_delete=models.CASCADE,
#         verbose_name="Норматив",
#     )
#     grade = models.IntegerField(
#         verbose_name="Оценка",
#         validators=[MinValueValidator(0)],
#     )
#     value = models.FloatField(
#         verbose_name="Значение",
#     )
#     level = models.ForeignKey(
#         Level,
#         on_delete=models.CASCADE,
#         verbose_name="Уровень",
#         null=True,
#         blank=True
#     )
#
#     def save(self, *args, **kwargs):
#         if isinstance(self.grade, float):
#             self.grade = round(self.grade)
#
#         student_class_number = self.student.student_class.number
#
#         try:
#             standard_value = Standard.objects.get(
#                 name=self.standard
#             )
#             self.level = Level.objects.get(
#                 standard=standard_value,
#                 level_number=student_class_number
#             )
#         except (Standard.DoesNotExist, Level.DoesNotExist):
#             self.level = None
#
#         super().save(*args, **kwargs)
#
#     def __str__(self) -> str:
#         return (
#             f"{self.student} - {self.standard} "
#             f"({self.value}, Оценка: {self.grade}, Уровень: {self.level})"
#         )

import logging


class StudentStandard(BaseModel):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        verbose_name="Ученик",
    )
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        verbose_name="Норматив",
    )
    grade = models.IntegerField(
        verbose_name="Оценка",
        validators=[MinValueValidator(0)],
    )
    value = models.FloatField(
        verbose_name="Значение",
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        verbose_name="Уровень",
        null=True
    )

    def save(self, *args, **kwargs):
        # Ensure grade is an integer
        if isinstance(self.grade, float):
            self.grade = round(self.grade)

        # Get the student's class number
        student_class_number = self.student.student_class.number

        # Initialize level to None
        self.level = None

        try:
            # Fetch the standard value by name
            standard_value = Standard.objects.get(name=self.standard.name)

            # Try to fetch the level corresponding to the standard and class number
            self.level = Level.objects.get(
                standard=standard_value,
                level_number=student_class_number,
                gender=self.student.gender,
            )
        except Standard.DoesNotExist:
            logging.error(f"Standard '{self.standard.name}' does not exist.")
        except Level.DoesNotExist:
            logging.error(
                f"Level for standard '{self.standard.name}' and class number '{student_class_number}' does not exist.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")

        # Proceed with saving the instance
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return (
            f"{self.student} - {self.standard} "
            f"({self.value}, Оценка: {self.grade}, Уровень: {self.level})"
        )
