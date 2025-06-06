from datetime import datetime

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models.functions import ExtractYear
from django_filters import rest_framework as filters

from ..models import Student


class StudentFilter(filters.FilterSet):
    """
    Фильтры для модели Student.
    Поддерживает фильтрацию по:
    - полу (gender)
    - классу обучения (student_class)
    - диапазону годов рождения (birth_year_min, birth_year_max)
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.has_patronymic = hasattr(Student, 'patronymic')

    gender = filters.CharFilter(field_name="gender", lookup_expr="iexact")
    birth_year_min = filters.NumberFilter(method='filter_birth_year_min',
                                          validators=[
                                              MinValueValidator(1920),
                                              MaxValueValidator(datetime.now().year)
                                          ])
    birth_year_max = filters.NumberFilter(method='filter_birth_year_max',
                                          validators=[
                                              MinValueValidator(1920),
                                              MaxValueValidator(datetime.now().year)
                                          ])
    student_class = filters.CharFilter(method='filter_student_class')
    full_name = filters.CharFilter(method='filter_full_name')

    class Meta:
        model = Student
        fields = ['gender', 'student_class', 'birth_year_min', 'birth_year_max', 'full_name']
        ordering = ['last_name', 'first_name', 'patronymic']

    def filter_birth_year_min(self, queryset, name, value):
        """Фильтрация по минимальному году рождения."""
        if value is None:
            return queryset
        return queryset.annotate(birth_year=ExtractYear('birthday')).filter(birth_year__gte=value)

    def filter_birth_year_max(self, queryset, name, value):
        """Фильтрация по максимальному году рождения."""
        if value is None:
            return queryset
        return queryset.annotate(birth_year=ExtractYear('birthday')).filter(birth_year__lte=value)

    def filter_student_class(self, queryset, name, value):
        """
        Фильтрация по классу обучения.
        Поддерживает:
        - Несколько конкретных классов (например, "4А,2Б")
        - Несколько параллелей (например, "4,2")
        """
        class_values = [val.strip() for val in value.split(',')]
        query = Q()

        for class_value in class_values:
            if not class_value:
                continue

            if class_value[-1].isalpha():
                number = class_value[:-1]
                class_letter = class_value[-1].upper()
                query |= Q(student_class__number=number, student_class__class_name=class_letter)
            else:
                query |= Q(student_class__number=class_value)

        return queryset.filter(query)

    def filter_full_name(self, queryset, name, value):
        """
        Фильтрация по ФИО.
        Поддерживает:
        - Поиск по любому количеству слов
        - Частичное совпадение
        - Нечувствительность к порядку слов
        """
        if not value:
            return queryset

        terms = [term.strip() for term in value.split() if term.strip()]
        if not terms:
            return queryset

        query = Q()

        for term in terms:
            term_query = (Q(first_name__icontains=term) |
                          Q(last_name__icontains=term))
            if self.has_patronymic:
                term_query |= Q(patronymic__icontains=term)
            query &= term_query

        return queryset.filter(query)
