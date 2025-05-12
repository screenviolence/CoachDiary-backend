import base64

import qrcode
from io import BytesIO

from django.http import HttpResponse
from django.template.loader import render_to_string

from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from xhtml2pdf import pisa

from common import utils
from common.permissions import IsTeacher, IsStudent
from standards.models import StudentStandard, Standard
from . import serializers
from .serializers import StudentSerializer
from .. import models

from django_filters import rest_framework as filters
from . import filters as custom_filters


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
            return models.Student.objects.filter(id=user.student.id)

        return models.Student.objects.none()

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

    @action(detail=False, methods=['get'])
    def generate_qr_codes_pdf(self, request):
        """
        Генерирует PDF с QR-кодами для ссылок-приглашений выбранного класса.
        """
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


@action(detail=False, methods=['get'])
def results(self, request, *args, **kwargs):
    class_ids = request.query_params.getlist('class_id[]')
    standard_id = request.query_params.get('standard_id')

    if not class_ids or not standard_id:
        return Response({"error": "Требуются class_id[] and standard_id"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        standard = Standard.objects.get(id=standard_id)
    except Standard.DoesNotExist:
        return Response({"error": "Норматив не найден."}, status=status.HTTP_404_NOT_FOUND)

    students = models.Student.objects.filter(student_class__id__in=class_ids,
                                             student_class__class_owner=request.user)
    resulting = StudentStandard.objects.filter(student__in=students, standard=standard)

    response_data = []
    for result in resulting:
        student_data = StudentSerializer(result.student).data
        result_data = {
            "value": result.value,
            "grade": result.grade
        }
        student_data.update(result_data)
        response_data.append(student_data)

    return Response(response_data, status=status.HTTP_200_OK)


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
