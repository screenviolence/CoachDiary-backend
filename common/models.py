from django.core.validators import MinValueValidator
from django.db import models
import uuid
from django_softdelete.models import SoftDeleteModel


class BaseModel(SoftDeleteModel, models.Model):
    """
    Общая базовая модель с UUID и датой создания.
    Можно расширить при необходимости (updated_at, soft-delete и т.д.).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

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
        verbose_name="Является ли это умением или нормативом",
        help_text="Если True, то это умение. Иначе - норматив",
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

    class Meta:
        abstract = True
        ordering = ['level_number']
