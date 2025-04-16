from django.db import transaction
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from students.models import Student
from common.permissions import IsTeacher
from standards import models
from .serializers import StudentResultSerializer, StandardSerializer, StudentStandardCreateSerializer, \
    StudentStandardSerializer


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
                location=OpenApiParameter.QUERY,
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


class StudentStandardsViewSet(viewsets.ViewSet):
    permission_classes = (IsTeacher,)
    serializer_class = StudentStandardSerializer

    def list(self, request, student_id=None):
        try:
            student = Student.objects.get(id=student_id, student_class__class_owner=request.user)
        except Student.DoesNotExist:
            raise PermissionDenied("У вас нет прав доступа к стандартам этого студента.")

        student_standards = models.StudentStandard.objects.filter(student=student)

        response_data = []
        for student_standard in student_standards:
            standard_data = {
                'Standard': {
                    'Id': student_standard.standard.id,
                    'Name': student_standard.standard.name,
                    'Has_numeric_value': student_standard.standard.has_numeric_value
                },
                'Level_number': student_standard.level.level_number if student_standard.level else None,
                'Value': student_standard.value,
                'Grade': student_standard.grade
            }
            response_data.append(standard_data)

        return Response(response_data)


class StudentsResultsViewSet(mixins.ListModelMixin, viewsets.ViewSet):
    permission_classes = (IsTeacher,)
    serializer_class = StudentResultSerializer

    def list(self, request, *args, **kwargs):
        class_ids = request.query_params.getlist('class_id[]')
        standard_id = request.query_params.get('standard_id')

        if not class_ids or not standard_id:
            return Response({"detail": "Требуются параметры class_id и standard_id."},
                            status=status.HTTP_400_BAD_REQUEST)

        students = Student.objects.filter(
            student_class__id__in=class_ids
        ).prefetch_related(
            'studentstandard_set__standard',
            'studentstandard_set__level_id'
        )

        serializer = StudentResultSerializer
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
                student_id = validated_data['student'].id
                standard_id = validated_data['standard'].id

                try:
                    student_result = models.StudentStandard.objects.get(
                        student_id=student_id, standard_id=standard_id,
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
