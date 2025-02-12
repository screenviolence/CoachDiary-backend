import json

from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from drf_spectacular.utils import extend_schema
from rest_framework import response, status, views, viewsets, mixins, permissions
from rest_framework.exceptions import ValidationError
from auth.users import models
from django.contrib.auth.hashers import check_password

from auth.users.api.serializers import UserSerializer, UserCreateSerializer, ChangePasswordSerializer, \
    ChangeUserDetailsSerializer


class UserLoginView(views.APIView):

    def get(self, request):
        """Return CSRF token."""
        return response.Response({"csrf": get_token(request)})

    def post(self, request):
        """Login user."""
        email = request.data.get("email")
        password = request.data.get("password")

        self._validate_email_and_password(email, password)

        user = authenticate(request, email=email, password=password)
        if user is None or not user.is_authenticated:
            return response.Response(
                {
                    "status": "error",
                    "details": "Email or password is not correct.",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        login(request, user)
        return response.Response(
            {
                "status": "ok",
                "details": "Logged In.",
            }
        )

    def _validate_email_and_password(self, email: str, password: str):
        """Check whether both fields are provided."""
        if not email and password:
            raise ValidationError("`email` field must be provided.")
        if email and not password:
            raise ValidationError("`password` field must be provided.")
        if not email and not password:
            raise ValidationError(
                "`email` and `password` fields must be provided.",
            )


class UserViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = UserCreateSerializer


@extend_schema(
    request=ChangePasswordSerializer,
    responses={200: UserSerializer}
)
@extend_schema(
    request=ChangePasswordSerializer,
    responses={200: UserSerializer}
)
class UserProfileViewSet(views.APIView):
    """Changes a password of current user."""
    serializer_class = UserSerializer
    permission_classes = (
        permissions.IsAuthenticated,
    )

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return response.Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # Handle password change
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return response.Response({"success": "Password successfully set"}, status=status.HTTP_200_OK)

    @extend_schema(
        request=ChangeUserDetailsSerializer,
        responses={200: UserSerializer}
    )
    def patch(self, request):
        # Handle name and/or email change
        serializer = ChangeUserDetailsSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = request.user
        if 'email' in serializer.validated_data:
            user.email = serializer.validated_data['email']
        if 'name' in serializer.validated_data:
            user.name = serializer.validated_data['name']
        user.save()
        return response.Response({"success": "User details successfully updated"}, status=status.HTTP_200_OK)


class UserLogoutView(views.APIView):
    permission_classes = (permissions.IsAuthenticated,)

    @extend_schema(
        responses={200: 'User successfully logged out'}
    )
    def post(self, request):
        """Logout user."""
        logout(request)
        return response.Response(
            {
                "status": "ok",
                "details": "Logged out successfully.",
            },
            status=status.HTTP_200_OK
        )