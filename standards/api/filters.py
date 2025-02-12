from django_filters import rest_framework as filters
from django.db.models.functions import ExtractYear
from ..models import Student, StudentClass
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator


class StudentFilter(filters.FilterSet):
    gender = filters.CharFilter(field_name="gender", lookup_expr="iexact")
    birthdate_lower = filters.NumberFilter(field_name="birthday", lookup_expr='gte', method='filter_by_year_gte')
    birthdate_upper = filters.NumberFilter(field_name="birthday", lookup_expr='lte', method='filter_by_year_lte')
    student_class = filters.CharFilter(field_name="student_class", method='filter_by_class')

    class Meta:
        model = Student
        fields = ['gender', 'student_class', 'birthdate_lower', 'birthdate_upper']

    def filter_by_year_gte(self, queryset, name, value):
        year_validator = [MinValueValidator(2000), MaxValueValidator(datetime.now().year)]
        for validator in year_validator:
            validator(value)
        return queryset.annotate(year=ExtractYear('birthday')).filter(year__gte=value)

    def filter_by_year_lte(self, queryset, name, value):
        return queryset.annotate(year=ExtractYear('birthday')).filter(year__lte=value)

    def filter_by_class(self, queryset, name, value):
        """
        Custom filter method to handle class filtering.
        Supports filtering by multiple specific classes (e.g., "4А,2А") or by multiple grades (e.g., "4,2").
        """
        # Split the input value into a list of classes/grades
        class_values = value.split(',')

        # Initialize the Q object to hold the OR conditions
        from django.db.models import Q
        query = Q()

        for class_value in class_values:
            class_value = class_value.strip()
            if class_value[-1].isdigit():
                # Filtering by grade
                query |= Q(student_class__number=class_value)
            else:
                # Filtering by specific class
                number = class_value[:-1]
                class_name = class_value[-1].upper()
                query |= Q(student_class__number=number, student_class__class_name=class_name)

        # Filter the queryset based on the constructed Q object
        return queryset.filter(query)