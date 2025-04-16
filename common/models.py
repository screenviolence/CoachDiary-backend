from django.core.validators import MinValueValidator
from django.db import models
from django_softdelete.models import SoftDeleteModel


class BaseModel(SoftDeleteModel, models.Model):
    """
    Общая базовая модель.
    """
    class Meta:
        abstract = True


class GenderChoices(models.TextChoices):
    MALE = 'm', 'Мужской'
    FEMALE = 'f', 'Женский'


class AbstractStandard(BaseModel):
    """
    Базовая модель для стандартов/нормативов
    """
    has_numeric_value = models.BooleanField(
        verbose_name="Является ли это физическим или техническим нормативом",
        help_text="Если True, то это физический норматив. Иначе - технический",
    )
    name = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class AbstractLevel(BaseModel):
    """
    Абстрактная модель для уровней
    """
    level_number = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Номер уровня"
    )
    gender = models.CharField(
        max_length=1,
        choices=GenderChoices,
        verbose_name="Пол"
    )
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
    is_lower_better = models.BooleanField(
        default=False,
        verbose_name="Чем меньше, тем лучше",
        help_text="Если отмечено, то меньшее значение считается лучшим (например, для времени)"
    )

    class Meta:
        abstract = True
        ordering = ['level_number']
