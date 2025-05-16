import datetime
import json
import uuid
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpResponse
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import response, status, viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.utils import timezone

from common.permissions import IsTeacher
from standards.models import Standard, StudentStandard, Level
from students.models import Invitation
from users import models
from users.api.serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer, \
    ChangeUserDetailsSerializer, ChangeUserEmailSerializer, UserLoginSerializer, UserInvitationSerializer, \
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
from students.api.serializers import InvitationDetailSerializer
from users.signals import send_confirmation_email
from users.utils import send_password_reset_email


class UserLoginView(viewsets.ViewSet):
    serializer_class = UserLoginSerializer

    @extend_schema(
        summary="Получение CSRF токена",
        description="Получение CSRF токена для защиты от CSRF атак"
    )
    def list(self, request):
        return response.Response({"csrf": get_token(request)})

    @extend_schema(
        summary="Вход пользователя (сессия браузера)",
        description="Вход пользователя в систему"
    )
    def create(self, request):
        """ Вход пользователя. """
        email = request.data.get("email")
        password = request.data.get("password")

        self._validate_email_and_password(email, password)

        user = authenticate(request, email=email, password=password)
        if user is None or not user.is_authenticated:
            return response.Response(
                {
                    "status": "ошибка",
                    "details": "Не правильно указана почта или пароль.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
        login(request, user)
        return response.Response(
            {
                "status": "успешно",
                "details": "Вход выполнен.",
            }
        )

    def _validate_email_and_password(self, email: str, password: str):
        """ Проверка, указаны ли эл. почта и пароль."""
        if not email and password:
            raise ValidationError("Нужно заполнить поле эл. почты.")
        if email and not password:
            raise ValidationError("Нужно заполнить поле пароля.")
        if not email and not password:
            raise ValidationError(
                "Нужно указать почту и пароль.",
            )


class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            'message': 'Регистрация успешна. Проверьте вашу почту для подтверждения аккаунта.'
        }, status=status.HTTP_201_CREATED)


class UserProfileViewSet(viewsets.GenericViewSet):
    """ Работа с профилем пользователя. """
    serializer_class = UserSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )

    @extend_schema(
        summary="Просмотр профиля пользователя"
    )
    def list(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Смена пароля пользователя",
        request=ChangePasswordSerializer,
    )
    @action(detail=False, methods=['put'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid()
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return response.Response({"success": "Пароль успешно установлен"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Смена ФИО",
        request=ChangeUserDetailsSerializer,
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=['patch'])
    def change_details(self, request):
        serializer = ChangeUserDetailsSerializer(data=request.data, context={'request': request})
        serializer.is_valid()
        user = request.user
        if 'first_name' in serializer.validated_data:
            user.first_name = serializer.validated_data['first_name']
        if 'last_name' in serializer.validated_data:
            user.last_name = serializer.validated_data['last_name']
        if 'patronymic' in serializer.validated_data:
            user.patronymic = serializer.validated_data['patronymic']

        user.save()
        return response.Response({"success": "Данные пользователя успешно обновлены"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cмена эл. почты",
        request=ChangeUserEmailSerializer,
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=['patch'])
    def change_email(self, request):
        serializer = ChangeUserEmailSerializer(data=request.data, context={'request': request})
        serializer.is_valid()
        user = request.user
        if 'email' in serializer.validated_data and serializer.validated_data['email'] != user.email:
            user.email = serializer.validated_data['email']

        user.save()
        return response.Response({"success": "Данные пользователя успешно обновлены"}, status=status.HTTP_200_OK)


class UserLogoutView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = None

    @extend_schema(
        summary="Выполнение выхода из аккаунта"
    )
    def create(self, request):
        logout(request)
        return response.Response(
            {
                "status": "success",
                "detail": "Вы вышли из аккаунта",
            },
            status=status.HTTP_200_OK
        )


class ResendConformationEmailView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = None

    @extend_schema(
        summary="Отправка повторного письма для подтверждения эл. почты",
        description="Отправляет повторное письмо для подтверждения эл. почты"
    )
    def list(self, request):
        user = request.user
        if user.is_email_verified:
            return Response(
                {"error": "Эл. почта уже подтверждена"},
                status=status.HTTP_400_BAD_REQUEST
            )

        send_confirmation_email(instance=user, created=True, sender=user)
        return Response(
            {"success": "Инструкции по подтверждению эл. почты отправлены на указанный адрес электронной почты"},
            status=status.HTTP_200_OK
        )

class PasswordResetViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        summary="Запрос на сброс пароля",
        request=PasswordResetRequestSerializer
    )
    @action(detail=False, methods=['post'])
    def request_reset(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid()
        email = serializer.validated_data['email']

        user = models.User.objects.filter(email=email).first()

        if not user:
            # Для безопасности не сообщаем, что пользователя не существует
            return Response(
                {
                    "success": "Если данная почта существует, инструкции по сбросу пароля отправлены на указанный адрес электронной почты"},
                status=status.HTTP_200_OK
            )

        reset_token = uuid.uuid4()

        user.password_reset_token = reset_token
        user.password_reset_expires = timezone.datetime.now(tz=timezone.timezone.utc) + timedelta(hours=24)
        user.save()
        send_password_reset_email(user)

        return Response(
            {
                "success": "Если данная почта существует, инструкции по сбросу пароля отправлены на указанный адрес электронной почты"},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Установка нового пароля",
        request=PasswordResetConfirmSerializer,
        description="Установка нового пароля по токену сброса пароля"
    )
    @action(detail=False, methods=['post'])
    def confirm_reset(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid()

        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        user = models.User.objects.filter(password_reset_token=token, password_reset_expires__gt=timezone.datetime.now(
            tz=timezone.timezone.utc)).first()

        if user is None:
            return Response(
                {"error": "Недействительный или устаревший токен сброса пароля"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)

        user.password_reset_token = None
        user.password_reset_expires = None
        user.save()

        return Response(
            {"success": "Пароль успешно изменен. Теперь вы можете войти в систему"},
            status=status.HTTP_200_OK
        )


class JoinByInvitationView(mixins.RetrieveModelMixin,
                           mixins.CreateModelMixin, viewsets.ViewSet):
    queryset = Invitation.objects.all()
    serializer_class = UserInvitationSerializer
    lookup_field = 'invite_code'

    @extend_schema(
        summary="Получение информации о студенте по коду приглашения",
        description="Получение информации о студенте по коду приглашения",
        responses={200: InvitationDetailSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        code = kwargs.get('invite_code')
        invitation = Invitation.objects.get(invite_code=code)
        if invitation.is_used:
            return Response(
                {"error": "Это приглашение уже использовано."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = InvitationDetailSerializer(invitation)
        return Response(serializer.data)

    @extend_schema(
        summary="Регистрация по коду приглашения",
        description="Регистрация ученика в качестве пользователя по коду приглашения",
        request=UserInvitationSerializer,
        responses={201: UserCreateSerializer}
    )
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = UserInvitationSerializer(data=request.data)
        if serializer.is_valid():
            invite_code = serializer.validated_data.pop('invite_code')
            invitation = get_object_or_404(Invitation, invite_code=invite_code, is_used=False)
            student = invitation.student

            user = serializer.save()

            student.user = user
            user.role = 'student'
            user.save()
            student.save()
            invitation.is_used = True
            invitation.save()

            return Response(
                {
                    "success": "Регистрация успешна. Проверьте вашу почту для подтверждения аккаунта."
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    @extend_schema(
        summary="Подтверждение эл. почты",
        description="Подтверждение эл. почты по токену",
    )
    def list(self, request, token):
        user = models.User.objects.filter(verification_token=token).first()
        if user is None:
            return Response({'error': 'Неверный токен подтверждения'}, status=status.HTTP_400_BAD_REQUEST)

        user.verification_token = None
        user.is_email_verified = True

        user.save()
        return Response({'message': 'Email успешно подтвержден'}, status=status.HTTP_200_OK)


class TeacherImportExportViewSet(viewsets.ViewSet):
    permission_classes = (IsTeacher,)

    @extend_schema(
        summary="Экспортирует данные преподавателя в формате JSON",
        description="Включает информацию о классах и учениках, которыми управляет преподаватель"
    )
    @action(detail=False, methods='get')
    def export_data(self, request):
        from students.models import StudentClass, Student

        user = request.user

        classes = StudentClass.objects.filter(class_owner=user)

        export_data = {
            'classes': []
        }
        standards = Standard.objects.filter(who_added=user)

        for standard in standards:
            standard_data = {
                'id': standard.id,
                'name': standard.name,
                'description': standard.description,
                'has_numeric_value': standard.has_numeric_value,
                'levels': []
            }

            for level in standard.get_levels():
                level_data = {
                    'id': level.id,
                    'level_number': level.level_number,
                    'is_lower_better': level.is_lower_better,
                    'gender': level.gender,
                    'low_value': level.low_value,
                    'middle_value': level.middle_value,
                    'high_value': level.high_value,
                }
                standard_data['levels'].append(level_data)

            export_data['standards'].append(standard_data)

        for class_obj in classes:
            class_data = {
                'number': class_obj.number,
                'class_name': class_obj.class_name,
                'is_archived': class_obj.is_archived,
                'students': []
            }

            students = Student.objects.filter(student_class=class_obj)

            for student in students:
                student_data = {
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'patronymic': student.patronymic,
                    'birthday': student.birthday.strftime('%Y-%m-%d'),
                    'gender': student.gender,
                    'standards_results': []
                }
                class_data['students'].append(student_data)

                student_standards = StudentStandard.objects.filter(student=student)

                for result in student_standards:
                    result_data = {
                        'standard_id': result.standard.id,
                        'standard_name': result.standard.name,
                        'value': result.value,
                        'grade': result.grade,
                        'level_id': result.level.id if result.level else None,
                        'level_number': result.level.level_number if result.level else None,
                        'date_recorded': result.date_recorded.strftime('%Y-%m-%d')
                    }
                    student_data['standards_results'].append(result_data)

                class_data['students'].append(student_data)

            export_data['classes'].append(class_data)

        filename = f"teacher_data_{user.last_name}_{user.first_name}_{datetime.datetime.now().strftime('%Y%m%d')}.json"

        response = HttpResponse(
            json.dumps(export_data, ensure_ascii=False, indent=4),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    @extend_schema(
        summary="Импортирует данные преподавателя из JSON-файла",
        description="Позволяет восстановить данные о классах, учениках, нормативах и их результатах"
    )
    @action(detail=False, methods='post')
    def import_data(self, request):
        from students.models import StudentClass, Student

        try:
            if 'file' not in request.FILES:
                return Response(
                    {'error': 'Файл не был предоставлен'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            uploaded_file = request.FILES['file']
            if not uploaded_file.name.endswith('.json'):
                return Response(
                    {'error': 'Файл должен быть в формате JSON'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            try:
                import_data = json.loads(uploaded_file.read().decode('utf-8'))
            except json.JSONDecodeError:
                return Response(
                    {'error': 'Неверный формат JSON-файла'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            if 'standards' not in import_data or 'classes' not in import_data:
                return Response(
                    {'error': 'Файл не содержит необходимые данные'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = request.user

            with transaction.atomic():
                imported_standards = 0
                imported_levels = 0
                imported_results = 0
                standards_mapping = {}
                levels_mapping = {}

                for standard_data in import_data.get('standards', []):
                    standard, standard_created = Standard.objects.get_or_create(
                        name=standard_data['name'],
                        who_added=user,
                        defaults={
                            'description': standard_data.get('description', ''),
                            'has_numeric_value': standard_data.get('has_numeric_value', True)
                        }
                    )

                    if standard_created:
                        imported_standards += 1

                    standards_mapping[standard_data['id']] = standard.id

                    for level_data in standard_data.get('levels', []):
                        level, level_created = Level.objects.get_or_create(
                            standard=standard,
                            level_number=level_data['level_number'],
                            gender=level_data['gender'],
                            defaults={
                                'is_lower_better': level_data.get('is_lower_better', False),
                                'low_value': level_data.get('low_value'),
                                'middle_value': level_data.get('middle_value'),
                                'high_value': level_data.get('high_value')
                            }
                        )

                        if level_created:
                            imported_levels += 1

                        levels_mapping[level_data['id']] = level.id

                imported_classes = 0
                imported_students = 0

                for class_data in import_data.get('classes', []):
                    class_obj, class_created = StudentClass.objects.get_or_create(
                        number=class_data['number'],
                        class_name=class_data['class_name'],
                        class_owner=user,
                        defaults={'is_archived': class_data.get('is_archived', False)}
                    )

                    if class_created:
                        imported_classes += 1

                    for student_data in class_data.get('students', []):
                        student, student_created = Student.objects.get_or_create(
                            first_name=student_data['first_name'],
                            last_name=student_data['last_name'],
                            patronymic=student_data.get('patronymic', ''),
                            student_class=class_obj,
                            defaults={
                                'birthday': datetime.datetime.strptime(student_data['birthday'], '%Y-%m-%d').date(),
                                'gender': student_data['gender'],
                            }
                        )

                        if student_created:
                            imported_students += 1

                        for result_data in student_data.get('standards_results', []):
                            standard_id = standards_mapping.get(result_data['standard_id'])
                            level_id = levels_mapping.get(result_data.get('level_id'))

                            if standard_id:
                                try:
                                    standard_obj = Standard.objects.get(id=standard_id)
                                    level_obj = Level.objects.get(id=level_id) if level_id else None

                                    result, result_created = StudentStandard.objects.get_or_create(
                                        student=student,
                                        standard=standard_obj,
                                        date_recorded=datetime.datetime.strptime(result_data['date_recorded'],
                                                                                 '%Y-%m-%d').date(),
                                        level=level_obj,
                                        defaults={
                                            'value': result_data['value'],
                                            'grade': result_data['grade']
                                        }
                                    )

                                    if result_created:
                                        imported_results += 1

                                except Exception as e:
                                    continue

                return Response({
                    'success': True,
                    'message': (f'Импорт завершен. Добавлено: классов: {imported_classes}, '
                                f'учеников: {imported_students}, стандартов: {imported_standards}, '
                                f'уровней: {imported_levels}, результатов: {imported_results}'),
                    'imported_classes': imported_classes,
                    'imported_students': imported_students,
                    'imported_standards': imported_standards,
                    'imported_levels': imported_levels,
                    'imported_results': imported_results
                })

        except Exception as e:
            return Response(
                {'error': f'Ошибка при импорте данных: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
