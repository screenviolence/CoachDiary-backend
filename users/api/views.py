from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import response, status, viewsets, mixins, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from students.models import Invitation
from users.api.serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer, \
    ChangeUserDetailsSerializer, ChangeUserEmailSerializer


class UserLoginView(viewsets.ViewSet):

    def list(self, request):
        """ Получение CSRF токена. """
        return response.Response({"csrf": get_token(request)})

    @action(detail=False, methods=['post'])
    def session_login(self, request):
        """ Вход пользователя. """
        email = request.data.get("email")
        password = request.data.get("password")

        self._validate_email_and_password(email, password)

        user = authenticate(request, email=email, password=password)
        if user is None or not user.is_authenticated:
            return response.Response(
                {
                    "статус": "ошибка",
                    "детали": "Не правильно указана почта или пароль.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return response.Response(
            {
                "статус": "успешно",
                "детали": "Вход выполнен.",
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
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return response.Response({"успех": "Пароль успешно установлен"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Смена ФИО",
        request=ChangeUserDetailsSerializer,
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=['patch'])
    def change_details(self, request):
        serializer = ChangeUserDetailsSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        if 'first_name' in serializer.validated_data:
            user.first_name = serializer.validated_data['first_name']
        if 'last_name' in serializer.validated_data:
            user.last_name = serializer.validated_data['last_name']
        if 'patronymic' in serializer.validated_data:
            user.patronymic = serializer.validated_data['patronymic']

        user.save()
        return response.Response({"успех": "Данные пользователя успешно обновлены"}, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Cмена эл. почты",
        request=ChangeUserEmailSerializer,
        responses={200: UserSerializer},
    )
    @action(detail=False, methods=['patch'])
    def change_email(self, request):
        serializer = ChangeUserEmailSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        if 'email' in serializer.validated_data and serializer.validated_data['email'] != user.email:
            user.email = serializer.validated_data['email']

        user.save()
        return response.Response({"успех": "Данные пользователя успешно обновлены"}, status=status.HTTP_200_OK)


class UserLogoutView(viewsets.ViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        summary="Выполнение выхода из аккаунта"
    )
    def logout(self, request):
        """Выполнение выхода из аккаунта."""
        logout(request)
        return response.Response(
            {
                "status": "успех",
                "details": "Вы вышли из аккаунта",
            },
            status=status.HTTP_200_OK
        )


class JoinByInvitationView(viewsets.ViewSet):
    """API для присоединения студента по коду приглашения"""

    def list(self, request, invite_code):
        """
        Получение информации о студенте по коду приглашения.
        """
        invitation = get_object_or_404(Invitation, invite_code=invite_code)
        student = invitation.student

        if invitation.is_used:
            return Response(
                {"error": "Это приглашение уже использовано."},
                status=status.HTTP_400_BAD_REQUEST
            )

        response_data = {
            "invitation": {
                "code": invitation.invite_code,
                "is_used": invitation.is_used
            },
            "student": {
                "id": student.id,
                "first_name": student.first_name,
                "last_name": student.last_name,
                "patronymic": student.patronymic or '',
            },
            "class": {
                "id": student.student_class.id,
                "number": student.student_class.number,
                "class_name": student.student_class.class_name
            }
        }

        return Response(response_data)

    @transaction.atomic
    def create(self, request, invite_code):
        """Обработка присоединения по коду приглашения"""
        invitation = get_object_or_404(Invitation, invite_code=invite_code, is_used=False)
        student = invitation.student

        user_data = request.data

        if not all(k in user_data for k in ['email', 'password', 'first_name', 'last_name']):
            return Response(
                {"error": "Необходимо указать email, пароль, имя и фамилию"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user_data['role'] = 'student'
        serializer = UserCreateSerializer(
            data=user_data,
            context={'invitation_registration': True}
        )

        if serializer.is_valid():
            user = serializer.save()

            student.user = user
            student.save()

            invitation.is_used = True
            invitation.save()

            return Response(
                {"message": "Регистрация прошла успешно", "user": serializer.data},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
