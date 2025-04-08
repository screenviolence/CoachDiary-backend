from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator

from common.models import AbstractLevel, AbstractStandard
from django.db import models

from users.models import User


class Standard(AbstractStandard):
    """
    Норматив/стандарт для оценки учеников.
    """
    who_added = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        verbose_name="Кто добавил норматив",
    )

    class Meta:
        verbose_name = "Норматив"
        verbose_name_plural = "Нормативы"

    def get_levels(self):
        return self.levels.all()


class Level(AbstractLevel):
    """
    Уровень норматива для определенного класса.
    """
    low_value = models.FloatField(
        validators=(
            MinValueValidator(0),
        ),
        verbose_name="Минимальное значение для уровня",
        null=True, blank=True
    )
    middle_value = models.FloatField(
        validators=(
            MinValueValidator(0),
        ),
        verbose_name="Среднее значение для уровня",
        null=True, blank=True
    )
    high_value = models.FloatField(
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
        verbose_name="Норматив",
    )

    def clean(self):
        if self.standard.has_numeric_value:
            if not all([self.low_value, self.middle_value, self.high_value]):
                raise ValidationError(
                    "Для нормативов с числовым значением необходимо указывать все уровневые значения."
                )
        else:
            if any([self.low_value, self.middle_value, self.high_value]):
                raise ValidationError(
                    "Для нормативов без числового значения не указываются уровневые значения."
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Уровень норматива"
        verbose_name_plural = "Уровни нормативов"
        unique_together = ['standard', 'level_number', 'gender']
        ordering = ['standard', 'level_number']

    def __str__(self):
        return f"Уровень {self.level_number} для {self.standard.name} ({self.get_gender_display()})"
