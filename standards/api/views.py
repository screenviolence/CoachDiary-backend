from django.db import transaction
from rest_framework import mixins, viewsets, permissions, status
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from . import serializers
from . import filters as custom_filters
from .serializers import StudentStandardSerializer, StudentSerializer, StudentResultSerializer
from .. import models


class StandardValueViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.StandardSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get_queryset(self):
        user = self.request.user
        return models.Standard.objects.filter(who_added_id=user.id)

    def perform_create(self, serializer):
        serializer.save(who_added_id=self.request.user.id)


class StudentViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.StudentSerializer
    queryset = models.Student.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = custom_filters.StudentFilter
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        return models.Student.objects.filter(student_class__class_owner=user)

    @action(detail=False, methods=['get'])
    def results(self, request):
        class_ids = request.query_params.getlist('class_id[]')
        standard_id = request.query_params.get('standard_id')

        if not class_ids or not standard_id:
            return Response({"error": "class_id[] and standard_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            standard = models.Standard.objects.get(id=standard_id)
        except models.Standard.DoesNotExist:
            return Response({"error": "Standard not found."}, status=status.HTTP_404_NOT_FOUND)

        students = models.Student.objects.filter(student_class__id__in=class_ids,
                                                 student_class__class_owner=request.user)
        results = models.StudentStandard.objects.filter(student__in=students, standard=standard)

        response_data = []
        for result in results:
            student_data = StudentSerializer(result.student).data
            result_data = {
                "value": result.value,
                "grade": result.grade
            }
            student_data.update(result_data)
            response_data.append(student_data)

        return Response(response_data, status=status.HTTP_200_OK)


class StudentClassViewset(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.StudentClassSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get_queryset(self):
        user = self.request.user
        return models.StudentClass.objects.filter(class_owner=user)

    def get_object(self):
        obj = super().get_object()
        if obj.class_owner != self.request.user:
            raise PermissionDenied("You do not have permission to access this object.")
        return obj


class StudentStandardsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def list(self, request, student_id=None):
        try:
            student = models.Student.objects.get(id=student_id, student_class__class_owner=request.user)
        except models.Student.DoesNotExist:
            raise PermissionDenied("You do not have permission to access this student's standards.")

        student_standards = models.StudentStandard.objects.filter(student=student)

        # Construct the desired output format
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


class StudentsResultsViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = StudentResultSerializer

    def list(self, request):
        class_ids = request.query_params.getlist('class_id[]')
        standard_id = request.query_params.get('standard_id')

        if not class_ids or not standard_id:
            return Response({"detail": "class_id and standard_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Get students within the specified classes
        students = models.Student.objects.filter(
            student_class__id__in=class_ids
        ).prefetch_related(
            'studentstandard_set__standard',
            'studentstandard_set__level_id'
        )

        # Serialize the results
        serializer = StudentResultSerializer
        return Response(serializer.data)


class StudentResultsCreateOrUpdateViewSet(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @action(detail=False, methods=['post'])
    @transaction.atomic
    def create_or_update(self, request, *args, **kwargs):
        data = request.data

        if not isinstance(data, list):
            return Response({"error": "Expected a list of objects."}, status=status.HTTP_400_BAD_REQUEST)

        response_data = []
        errors = []

        for entry in data:
            serializer = serializers.StudentStandardCreateSerializer(data=entry)
            if serializer.is_valid():
                validated_data = serializer.validated_data
                student_id = validated_data['student_id']
                standard_id = validated_data['standard_id']

                try:
                    student_result = models.StudentStandard.objects.get(
                        student_id=student_id, standard_id=standard_id,
                    )
                    # If it exists, update it
                    update_serializer = serializers.StudentStandardCreateSerializer(
                        student_result, data=entry, partial=True
                    )
                    if update_serializer.is_valid():
                        update_serializer.save()
                        response_data.append({
                            "detail": "Student result record updated successfully.",
                            "data": update_serializer.data
                        })
                    else:
                        errors.append(update_serializer.errors)
                except models.StudentStandard.DoesNotExist:
                    # If it doesn't exist, create a new one
                    student_result = serializer.save()
                    response_data.append({
                        "detail": "Student result record created successfully.",
                        "data": serializers.StudentStandardCreateSerializer(student_result).data
                    })
            else:
                errors.append(serializer.errors)

        if errors:
            return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_200_OK)
