import datetime
import json
import uuid
from datetime import timedelta

import pandas as pd
import io

from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.http import HttpResponse
from django.middleware.csrf import get_token
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import response, status, viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.utils import timezone

from common.excel_utils import write_headers_and_data, create_excel_formats
from common.permissions import IsTeacher
from standards.models import Standard, StudentStandard, Level
from students.api.serializers import InvitationDetailSerializer
from students.models import Invitation
from users import models
from users.api.serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer, \
    ChangeUserDetailsSerializer, ChangeUserEmailSerializer, UserLoginSerializer, UserInvitationSerializer, \
    PasswordResetRequestSerializer, PasswordResetConfirmSerializer
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

    @extend_schema(
        summary="Регистрация",
        description="Создание нового пользователя"
    )
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
    @action(detail=False, methods=['patch'])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
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
    @action(detail=False, methods=['get'])
    def export_data(self, request):
        from students.models import StudentClass

        user = request.user

        classes = StudentClass.objects.filter(class_owner=user).prefetch_related('students')
        standards = Standard.objects.filter(who_added=user).prefetch_related('levels')

        student_ids = []
        for class_obj in classes:
            for student in class_obj.students.all():
                student_ids.append(student.id)

        all_student_standards = StudentStandard.objects.filter(
            student_id__in=student_ids
        ).select_related('standard', 'level')

        student_results = {}
        for result in all_student_standards:
            if result.student_id not in student_results:
                student_results[result.student_id] = []
            student_results[result.student_id].append(result)

        export_data = {
            'classes': [],
            'standards': []
        }

        for standard in standards:
            standard_data = {
                'id': standard.id,
                'name': standard.name,
                'description': standard.description,
                'has_numeric_value': standard.has_numeric_value,
                'levels': []
            }

            for level in standard.levels.all():
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

            for student in class_obj.students.all():
                student_data = {
                    'first_name': student.first_name,
                    'last_name': student.last_name,
                    'patronymic': student.patronymic,
                    'birthday': student.birthday.strftime('%Y-%m-%d'),
                    'gender': student.gender,
                    'standards_results': []
                }

                for result in student_results.get(student.id, []):
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

        response = HttpResponse(
            json.dumps(export_data, ensure_ascii=False, indent=4),
            content_type='application/json'
        )
        response['Content-Disposition'] = f'attachment; filename="teacher_data_export_{user.id}.json"'

        return response

    @extend_schema(
        summary="Импортирует данные преподавателя из JSON-файла",
        description="Позволяет восстановить данные о классах, учениках, нормативах и их результатах"
    )
    @action(detail=False, methods=['post'])
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
                existing_standards = {
                    s.name: s for s in Standard.objects.filter(who_added=user)
                }

                existing_levels = {}
                for level in Level.objects.filter(standard__who_added=user):
                    key = (level.standard_id, level.level_number, level.gender)
                    existing_levels[key] = level

                existing_classes = {
                    (c.number, c.class_name): c
                    for c in StudentClass.objects.filter(class_owner=user)
                }

                existing_students = {}
                for student in Student.objects.filter(student_class__class_owner=user):
                    key = (student.first_name, student.last_name, student.patronymic, student.student_class_id)
                    existing_students[key] = student

                existing_results = set()
                for result in StudentStandard.objects.filter(
                        student__student_class__class_owner=user
                ).values_list('student_id', 'standard_id', 'date_recorded'):
                    existing_results.add((result[0], result[1], result[2]))

                imported_standards = 0
                imported_levels = 0
                imported_results = 0
                imported_classes = 0
                imported_students = 0

                students_mapping = {}
                standards_mapping = {}
                levels_mapping = {}

                for standard_data in import_data.get('standards', []):
                    standard = existing_standards.get(standard_data['name'])

                    if not standard:
                        standard = Standard(
                            name=standard_data['name'],
                            who_added=user,
                            description=standard_data.get('description', ''),
                            has_numeric_value=standard_data.get('has_numeric_value', True)
                        )
                        standard.save()
                        existing_standards[standard.name] = standard
                        imported_standards += 1

                    standards_mapping[standard_data['id']] = standard.id

                    levels_to_create = []
                    for level_data in standard_data.get('levels', []):
                        key = (standard.id, level_data['level_number'], level_data['gender'])
                        if key not in existing_levels:
                            levels_to_create.append(
                                Level(
                                    standard=standard,
                                    level_number=level_data['level_number'],
                                    gender=level_data['gender'],
                                    is_lower_better=level_data.get('is_lower_better', False),
                                    low_value=level_data.get('low_value'),
                                    middle_value=level_data.get('middle_value'),
                                    high_value=level_data.get('high_value')
                                )
                            )

                    if levels_to_create:
                        Level.objects.bulk_create(levels_to_create)
                        imported_levels += len(levels_to_create)

                        for level in Level.objects.filter(standard=standard):
                            key = (level.standard_id, level.level_number, level.gender)
                            existing_levels[key] = level
                            levels_mapping[level_data['id']] = level.id

                for class_data in import_data.get('classes', []):
                    key = (class_data['number'], class_data['class_name'])
                    class_obj = existing_classes.get(key)

                    if not class_obj:
                        class_obj = StudentClass(
                            number=class_data['number'],
                            class_name=class_data['class_name'],
                            class_owner=user,
                            is_archived=class_data.get('is_archived', False)
                        )
                        class_obj.save()
                        existing_classes[key] = class_obj
                        imported_classes += 1

                    students_to_create = []
                    results_to_create = []

                    for student_data in class_data.get('students', []):
                        key = (
                            student_data['first_name'],
                            student_data['last_name'],
                            student_data.get('patronymic', ''),
                            class_obj.id
                        )
                        student = existing_students.get(key)

                        if not student:
                            student = Student(
                                first_name=student_data['first_name'],
                                last_name=student_data['last_name'],
                                patronymic=student_data.get('patronymic', ''),
                                student_class=class_obj,
                                birthday=datetime.datetime.strptime(student_data['birthday'], '%Y-%m-%d').date(),
                                gender=student_data['gender']
                            )
                            students_to_create.append(student)
                            students_mapping[key] = student

                        student_data['key'] = key
                        student_data['student_obj'] = student

                    if students_to_create:
                        batch_size = 1000
                        for i in range(0, len(students_to_create), batch_size):
                            batch = students_to_create[i:i + batch_size]
                            Student.objects.bulk_create(batch)
                            imported_students += len(batch)

                        for key, student in students_mapping.items():
                            student_refreshed = Student.objects.get(
                                first_name=student.first_name,
                                last_name=student.last_name,
                                patronymic=student.patronymic,
                                student_class=student.student_class
                            )
                            existing_students[key] = student_refreshed

                    for student_data in class_data.get('students', []):
                        key = student_data['key']
                        student = existing_students[key]

                        for result_data in student_data.get('standards_results', []):
                            standard_id = standards_mapping.get(result_data['standard_id'])
                            level_id = levels_mapping.get(result_data.get('level_id'))

                            if standard_id:
                                date_recorded = datetime.datetime.strptime(
                                    result_data['date_recorded'], '%Y-%m-%d'
                                ).date()

                                result_key = (student.id, standard_id, date_recorded)
                                if result_key not in existing_results:
                                    try:
                                        result = StudentStandard(
                                            student=student,
                                            standard_id=standard_id,
                                            date_recorded=date_recorded,
                                            level_id=level_id,
                                            value=result_data['value'],
                                            grade=result_data['grade']
                                        )
                                        results_to_create.append(result)
                                        existing_results.add(result_key)
                                        imported_results += 1
                                    except Exception:
                                        continue

                    if results_to_create:
                        batch_size = 1000
                        for i in range(0, len(results_to_create), batch_size):
                            batch = results_to_create[i:i + batch_size]
                            StudentStandard.objects.bulk_create(batch)

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

    @extend_schema(
        summary="Экспорт данных в формате XLSX",
        description="Создает Excel-файл с данными по нормативам для всех учеников",
        parameters=[
            OpenApiParameter(
                name='include_norms',
                type=OpenApiTypes.BOOL,
                location='query',
                required=False,
                description='Включать лист с таблицей нормативов',
                default=True
            ),
            OpenApiParameter(
                name='include_results',
                type=OpenApiTypes.BOOL,
                location='query',
                required=False,
                description='Включать сводный лист с итоговыми результатами',
                default=True
            ),
            OpenApiParameter(
                name='include_standards',
                type=OpenApiTypes.BOOL,
                location='query',
                required=False,
                description='Включать отдельные листы для каждого норматива',
                default=True
            )
        ]
    )
    @action(detail=False, methods=['get'])
    def export_xlsx(self, request):
        from students.models import StudentClass

        include_norms = request.query_params.get('include_norms', 'true').lower() == 'true'
        include_results = request.query_params.get('include_results', 'true').lower() == 'true'
        include_standards = request.query_params.get('include_standards', 'true').lower() == 'true'

        user = request.user
        standards = Standard.objects.filter(who_added=user)
        classes = StudentClass.objects.filter(class_owner=user)

        output = io.BytesIO()

        with pd.ExcelWriter(output,engine_kwargs={"options": {"nan_inf_to_errors": True}}, engine='xlsxwriter') as writer:
            formats = create_excel_formats(writer.book)

            if include_norms:
                self._create_norms_table(writer, standards, formats)

            if include_results:
                self._create_results_sheet(writer, standards, classes, formats)

            if include_standards:
                for standard in standards:
                    self._create_standard_sheet(writer, standard, classes, formats)

        output.seek(0)
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename="standards_export.xlsx"'
        return response

    def _create_norms_table(self, writer, standards, formats):
        """Создает лист с таблицей нормативов."""
        norm_data = []
        columns = ["норматив"]
        for class_num in range(1, 12):
            for gender in ['мальчики', 'девочки']:
                for level in ['повышенный', 'высокий', 'средний']:
                    columns.append(f"{class_num} класс {gender} {level}")

        standards_filtered = standards.filter(has_numeric_value=True)
        levels = Level.objects.filter(standard__in=standards_filtered).select_related('standard')
        levels_dict = {}
        for level in levels:
            key = (level.standard.id, level.level_number, level.gender)
            levels_dict[key] = level

        for standard in standards_filtered:
            row = [standard.name]
            for class_num in range(1, 12):
                for gender in ['m', 'f']:
                    level = levels_dict.get((standard.id, class_num, gender))
                    if level:
                        row.extend([level.high_value, level.middle_value, level.low_value])
                    else:
                        row.extend([None, None, None])
            norm_data.append(row)

        df_norms = pd.DataFrame(norm_data, columns=columns)
        df_norms = df_norms.replace([float('inf'), -float('inf'), pd.NA, pd.NaT], None)

        df_norms.to_excel(writer, sheet_name="Таблица нормативов", index=False)

        worksheet = writer.sheets["Таблица нормативов"]
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(1, len(columns), 12)

        write_headers_and_data(worksheet, df_norms, formats)

    def _create_results_sheet(self, writer, standards, classes, formats):
        """Создает сводный лист с итоговыми результатами всех студентов."""
        from students.models import Student

        students = Student.objects.filter(student_class__in=classes).select_related(
            'student_class').order_by(
            'student_class__number', 'student_class__class_name', 'last_name', 'first_name')

        student_ids = [student.id for student in students]
        all_results = StudentStandard.objects.filter(
            student_id__in=student_ids,
            standard__in=standards
        ).select_related('level', 'standard').order_by('-date_recorded')

        results_map = {}
        for result in all_results:
            if result.level:
                key = (result.student_id, result.standard_id, result.level.level_number)
                if key not in results_map:
                    results_map[key] = result

        data = []
        columns = ["№", "ФИО", "Пол", "Класс", "Дата рождения"]

        for class_num in range(1, 12):
            columns.append(f"Итого {class_num} класс")

        for i, student in enumerate(students, 1):
            gender_display = "ж" if student.gender == 'f' else "м"
            class_name = f"{student.student_class.number}{student.student_class.class_name}"

            row = [
                i,
                f"{student.full_name}",
                gender_display,
                class_name,
                student.birthday.strftime("%d.%m.%Y")
            ]

            for class_num in range(1, 12):
                class_grades = []

                for standard in standards:
                    key = (student.id, standard.id, class_num)
                    if key in results_map and results_map[key].grade is not None:
                        class_grades.append(results_map[key].grade)

                if class_grades:
                    try:
                        avg_class_grade = sum(class_grades) / len(class_grades)
                        row.append(round(avg_class_grade, 1))
                    except (OverflowError, ValueError):
                        row.append(None)
                else:
                    row.append('')

            data.append(row)

        df = pd.DataFrame(data, columns=columns)
        df = df.replace([float('inf'), -float('inf'), pd.NA, pd.NaT], None)
        df = df.where(pd.notna(df), None)

        df.to_excel(writer, sheet_name="Итоговые результаты", index=False)

        worksheet = writer.sheets["Итоговые результаты"]
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 25)
        worksheet.set_column(2, 2, 6)
        worksheet.set_column(3, 3, 8)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, len(columns), 15)

        write_headers_and_data(worksheet, df, formats, gender_col=2)

    def _create_standard_sheet(self, writer, standard, classes, formats):
        """Создает лист для конкретного норматива."""
        from students.models import Student

        students = Student.objects.filter(student_class__in=classes).select_related(
            'student_class').order_by('student_class__number', 'student_class__class_name')

        student_ids = [student.id for student in students]
        results = StudentStandard.objects.filter(
            student_id__in=student_ids,
            standard=standard
        ).select_related('level').order_by('level__level_number')

        results_by_student = {}
        for result in results:
            if not result.level:
                continue
            if result.student_id not in results_by_student:
                results_by_student[result.student_id] = {}
            results_by_student[result.student_id][result.level.level_number] = result

        student_data = []
        columns = ["№", "ФИО", "пол", "класс", "д.р."]
        for class_num in range(1, 12):
            columns.append(str(class_num))
            columns.append(f"{class_num}ур")

        for i, student in enumerate(students, 1):
            gender_display = "ж" if student.gender == 'f' else "м"
            class_name = f"{student.student_class.number}{student.student_class.class_name}"

            row = [
                i,
                f"{student.full_name}",
                gender_display,
                class_name,
                student.birthday.strftime("%d.%m.%Y")
            ]

            student_results = results_by_student.get(student.id, {})

            for class_num in range(1, 12):
                if class_num in student_results:
                    result = student_results[class_num]
                    value = result.value if result.value not in (float('inf'), -float('inf')) else None
                    row.append(value)
                    row.append(result.grade)
                else:
                    row.append(0)
                    row.append('')

            student_data.append(row)

        df_students = pd.DataFrame(student_data, columns=columns)
        df_students = df_students.replace([float('inf'), -float('inf'), pd.NA, pd.NaT], None)

        sheet_name = standard.name[:31]
        df_students.to_excel(writer, sheet_name=sheet_name, index=False)

        worksheet = writer.sheets[sheet_name]
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 25)
        worksheet.set_column(2, len(columns), 10)

        write_headers_and_data(worksheet, df_students, formats, gender_col=2)
