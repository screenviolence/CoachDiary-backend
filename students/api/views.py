from django.http import HttpResponse
from django.template.loader import render_to_string
from django_filters import rest_framework as filters
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from common import utils
from common.permissions import IsTeacher
from standards.models import StudentStandard, Standard
from . import filters as custom_filters
from . import serializers
from .serializers import StudentSerializer
from .. import models


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

        if hasattr(user, 'role') and user.role == 'teacher':
            return models.Student.objects.filter(student_class__class_owner=user)
        elif hasattr(user, 'role') and user.role == 'student' and hasattr(user, 'student'):
            return models.Student.global_objects.filter(id=user.student.id)
        return models.Student.objects.none()

    @extend_schema(
        summary="Получение списка студентов",
        description="Возвращает список студентов, доступных для текущего пользователя. "
                    "Учителя видят всех студентов в своих классах, студенты видят только себя.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получение информации о студенте",
        description="Возвращает информацию о конкретном студенте. "
                    "Учителя могут видеть информацию о студентах в своих классах, "
                    "студенты видят только себя.",
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()

        if hasattr(request.user, 'role') and request.user.role == 'teacher':
            if instance.student_class.class_owner != request.user:
                return Response(
                    {"error": "У вас нет доступа к этому студенту"},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif hasattr(request.user, 'role') and request.user.role == 'student':
            if not hasattr(request.user, 'student') or request.user.student.id != instance.id:
                return Response(
                    {"error": "У вас нет доступа к этому студенту"},
                    status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @extend_schema(
        summary="Удаление студента",
        description="Удаляет студента из базы данных. "
                    "Учителя могут удалять студентов в своих классах, "
                    "студенты не могут удалять себя. "
                    "Если у студента был аккаунт, то он всё равно сможет входить в систему "
                    "и смотреть свои данные и результаты на момент удаления. "
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Создание нового студента",
        description="Создаёт нового студента в базе данных. "
                    "Учителя могут создавать студентов в своих классах, "
                    "студенты не могут создавать себя.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Обновление информации о студенте",
        description="Обновляет информацию о студенте. "
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление информации о студенте",
        description="Частично обновляет информацию о студенте. "
                    "Позволяет обновлять только некоторые поля.",
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Генерация PDF с QR-кодами для студентов класса",
        description="Генерирует PDF-файл, содержащий QR-коды для каждого студента в классе. "
                    "QR-коды содержат ссылки на приглашения для регистрации в роли обучающегося.",
        parameters=[
            OpenApiParameter(
                name='class_id',
                required=True,
                type=OpenApiTypes.INT,
                description="ID класса, для которого нужно сгенерировать QR-коды.")
        ],
        responses={
            200: OpenApiResponse
                (response=OpenApiTypes.BINARY)
        },
    )
    @action(detail=False, methods=['get'])
    def generate_qr_codes_pdf(self, request):
        import base64
        import qrcode
        from io import BytesIO
        from xhtml2pdf import pisa

        class_id = request.query_params.get('class_id')
        if not class_id:
            return Response(
                {"error": "Необходимо указать параметр class_id"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            student_class = models.StudentClass.objects.get(id=class_id)
            if student_class.class_owner != request.user:
                return Response(
                    {"error": "У вас нет доступа к этому классу"},
                    status=status.HTTP_403_FORBIDDEN
                )
        except Exception:
            return Response(
                {"error": f"Класс не найден"},
                status=status.HTTP_404_NOT_FOUND
            )

        students = models.Student.objects.filter(student_class=student_class)

        qr_data = []
        for student in students:
            if hasattr(student, 'invitation') and not student.invitation.is_used:
                try:
                    invitation_link = student.invitation.get_join_link()
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(invitation_link)
                    qr.make(fit=True)
                    img = qr.make_image(fill_color="black", back_color="white")

                    buffer = BytesIO()
                    img.save(buffer, format="PNG")
                    qr_image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

                    qr_data.append({
                        'invite_code': student.invitation.invite_code,
                        'initials': student.initials,
                        'invitation_link': invitation_link,
                        'qr_code': qr_image_base64,
                    })
                except Exception as e:
                    print(f"Ошибка при создании QR-кода: {e}")

        html_string = render_to_string('qr_codes_template.html', {
            'student_class': student_class,
            'qr_data': qr_data,
        })

        result = BytesIO()

        pisa_status = pisa.CreatePDF(
            html_string,
            dest=result,
            encoding='UTF-8',
            link_callback=utils.link_callback
        )

        if pisa_status.err:
            return Response(
                {"error": f"Ошибка при создании PDF: {pisa_status.err}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        result.seek(0)
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="qr_codes_class_{class_id}.pdf"'

        return response


class StudentClassViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = serializers.StudentClassSerializer
    permission_classes = (
        IsTeacher,
    )
    queryset = models.StudentClass.objects.all()

    def get_queryset(self):
        user = self.request.user
        return models.StudentClass.objects.filter(class_owner=user)

    def get_object(self):
        obj = super().get_object()
        if obj.class_owner != self.request.user:
            raise PermissionDenied("У вас нет прав доступа к этому классу.")
        return obj

    @extend_schema(
        summary="Получение списка классов",
        description="Возвращает список классов, доступных для текущего пользователя. "
                    "Учителя видят только свои классы.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получение информации о классе",
        description="Возвращает информацию о конкретном классе. "
                    "Учителя могут видеть информацию только о своих классах.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Удаление класса",
        description="Удаляет класс из базы данных вместе с его студентами. "
                    "Учителя могут удалять только свои классы.",
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @extend_schema(
        summary="Переводит все классы на следующий год обучения",
        description="Переводит все классы текущего пользователя на следующий год обучения. "
                    "Если класс 11, то он удаляется.",
        request=None,
    )
    @action(detail=False, methods=['post'])
    def promote(self, request, *args, **kwargs):
        user = request.user

        models.StudentClass.objects.filter(class_owner=user, number=11).delete()

        classes_to_update = models.StudentClass.objects.filter(class_owner=user)
        for student_class in classes_to_update:
            student_class.number += 1
            student_class.save()

        updated_classes = models.StudentClass.objects.filter(class_owner=user)

        serializer = serializers.StudentClassSerializer(updated_classes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
