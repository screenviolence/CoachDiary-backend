from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from students.models import Student
from common.permissions import IsTeacher
from standards import models
from .serializers import StudentResultSerializer, StandardSerializer, StudentStandardCreateSerializer, \
    StudentStandardSerializer, StudentStandardsResponseSerializer
from django.db.models import F


class StandardValueViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StandardSerializer
    permission_classes = (
        IsTeacher,
    )

    @extend_schema(
        description="Удаляет уровни норматива для указанного номера класса (для обоих полов)",
        parameters=[
            OpenApiParameter(
                name='level_number',
                type=OpenApiTypes.INT,
                location='query',
                description='Номер уровня (класса), для которого нужно удалить норматив',
                required=True
            ),
        ]
    )
    @action(detail=True, methods=['delete'])
    def remove_level(self, request, pk=None):
        standard = self.get_object()
        level_number = request.query_params.get('level_number')

        if not level_number:
            return Response(
                {"detail": "Необходимо указать параметр level_number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        levels_to_delete = standard.levels.filter(level_number=level_number)

        if levels_to_delete.exists():
            deleted_count = levels_to_delete.count()
            levels_to_delete.delete()
            return Response(
                {"detail": f"Удалено уровней: {deleted_count}"},
                status=status.HTTP_204_NO_CONTENT
            )
        else:
            return Response(
                {"detail": f"Уровни с номером {level_number} не найдены для данного норматива"},
                status=status.HTTP_404_NOT_FOUND
            )

    def get_queryset(self):
        user = self.request.user
        return models.Standard.objects.filter(who_added_id=user.id)

    def perform_create(self, serializer):
        """
        Проверяет существование норматива с таким же именем.
        Если норматив существует, добавляет к нему новые уровни вместо создания нового.
        """
        standard_data = serializer.validated_data
        standard_name = standard_data.get('name')

        existing_standard = models.Standard.objects.filter(name=standard_name).first()

        if existing_standard:
            levels_data = standard_data.get('levels', [])

            for level_data in levels_data:
                level_exists = models.Level.objects.filter(
                    standard=existing_standard,
                    level_number=level_data.get('level_number'),
                    gender=level_data.get('gender')
                ).exists()

                if not level_exists:
                    models.Level.objects.create(
                        standard=existing_standard,
                        **level_data
                    )

            return existing_standard
        else:
            serializer.save(who_added_id=self.request.user.id)

    def perform_update(self, serializer):
        """
        Метод обновления норматива для сохранения связей с результатами студентов
        """
        with transaction.atomic():
            instance = self.get_object()
            old_name = instance.name
            new_name = serializer.validated_data.get('name', old_name)

            if hasattr(models, 'StudentStandard'):
                related_records = list(models.StudentStandard.objects.filter(standard=instance))
            else:
                related_records = []

            updated_standard = serializer.save()

            for record in related_records:
                record.standard = updated_standard
                record.save()

            return updated_standard


class StudentStandardsViewSet(viewsets.ViewSet):
    serializer_class = StudentStandardsResponseSerializer
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Результаты ученика по его нормативам",
        description="Отображает результаты ученика по его нормативам",
        parameters=[
            OpenApiParameter(
                name='level_number',
                type=OpenApiTypes.INT,
                location='query',
                description='Номер уровня (класса), для которого нужно вывести оценки. По умолчанию - текущий класс ученика',
                required=False
            ),
        ]
    )
    def list(self, request, student_id=None):
        if hasattr(request.user, 'role') and request.user.role == 'teacher':
            student = Student.objects.filter(id=student_id, student_class__class_owner=request.user).first()
        elif hasattr(request.user, 'role') and request.user.role == 'student':
            if not hasattr(request.user, 'student') or str(request.user.student.id) != str(student_id):
                raise PermissionDenied("У вас нет прав доступа к стандартам этого студента.")
            student = request.user.student
        else:
            raise PermissionDenied("У вас нет прав доступа к стандартам студентов.")

        student_standards = models.StudentStandard.objects.filter(student=student)

        level_number = request.query_params.get('level_number')
        if level_number:
            try:
                level_number = int(level_number)
            except ValueError:
                return Response(
                    {"detail": "Параметр level_number должен быть числом"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            level_number = student.student_class.number

        filtered_standards = student_standards.filter(level__level_number=level_number)

        numeric_standards = [s for s in filtered_standards if s.standard.has_numeric_value]
        if numeric_standards:
            summary_grade = sum(s.grade for s in numeric_standards) / len(numeric_standards)
        else:
            summary_grade = 0

        response_data = {
            'standards': filtered_standards,
            'summary_grade': summary_grade,
            'level_number': level_number
        }

        serializer = StudentStandardsResponseSerializer(response_data)
        return Response(serializer.data)


class StudentsResultsViewSet(mixins.ListModelMixin, viewsets.ViewSet):
    permission_classes = (IsTeacher,)
    serializer_class = StudentResultSerializer

    @extend_schema(
        summary="Результаты учеников из выбранных классов по выбранным нормативам",
        description="Отображает результаты учеников из выбранного одного или нескольких классов по выбранным нормативам",
        parameters=[
            OpenApiParameter(
                name='class_id[]',
                type=OpenApiTypes.INT,
                location='query',
                description='Идентификаторы классов, для которых нужно вывести результаты учеников',
                required=True
            ),
            OpenApiParameter(
                name='standard_id[]',
                type=OpenApiTypes.INT,
                location='query',
                description='Идентификаторы нормативов, по которым нужно вывести результаты',
                required=True
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        class_ids = request.query_params.getlist('class_id[]')
        standard_ids = request.query_params.getlist('standard_id[]')

        if not class_ids or not standard_ids:
            return Response({"detail": "Требуются параметры class_id[] и standard_id[]."},
                            status=status.HTTP_400_BAD_REQUEST)

        students = Student.objects.filter(
            student_class__id__in=class_ids,
            student_class__class_owner=request.user
        )
        serializer = StudentResultSerializer(
            students,
            many=True,
            context={'standard_ids': standard_ids}
        )

        return Response(serializer.data)


class StudentResultsCreateOrUpdateViewSet(viewsets.ViewSet):
    permission_classes = (IsTeacher,)
    serializer_class = StudentStandardCreateSerializer

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        data = request.data

        if not isinstance(data, list):
            return Response({"error": "Ожидается список объектов."}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        errors = []

        for entry in data:
            serializer = StudentStandardCreateSerializer(data=entry)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                student = validated_data['student']
                student_id = validated_data['student'].id
                standard_id = validated_data['standard'].id
                level_number = validated_data.get('level_number', student.student_class.number)
                try:
                    student_result = models.StudentStandard.objects.get(
                        student_id=student_id, standard_id=standard_id,
                        level__level_number=level_number
                    )
                    update_serializer = StudentStandardCreateSerializer(
                        student_result, data=entry, partial=True
                    )
                    if update_serializer.is_valid():
                        update_serializer.save()
                        response_data.append({
                            "detail": "Запись результата студента успешно обновлена.",
                            "data": update_serializer.data
                        })
                    else:
                        errors.append(update_serializer.errors)
                except models.StudentStandard.DoesNotExist:
                    student_result = serializer.save()
                    response_data.append({
                        "detail": "Запись результата студента успешно создана.",
                        "data": StudentStandardCreateSerializer(student_result).data
                    })
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)
