from django.contrib.auth.hashers import check_password
from rest_framework import serializers

from students.models import Invitation
from .. import models


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = models.User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "patronymic",
            "full_name",
            "role",
        )

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.role == 'student':
            representation['id'] = instance.student.id
        return representation


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    patronymic = serializers.CharField(required=False, allow_blank=True)
    role = serializers.CharField(required=False, read_only=True)

    class Meta:
        model = models.User
        fields = [
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'patronymic',
            'role'
        ]

    def validate(self, data):
        if models.User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("Эта эл. почта уже используется")
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        patronymic = validated_data.pop('patronymic', None)
        role = 'teacher'

        if self.context.get('invitation_registration'):
            role = 'student'

        user = models.User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            role=role
        )

        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("Пароли не совпадают.")
        if not check_password(data['current_password'], self.context['request'].user.password):
            raise serializers.ValidationError("Текущий пароль неверный.")
        return data


class ChangeUserDetailsSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    patronymic = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if not data.get('first_name'):
            raise serializers.ValidationError("Нужно указать имя")
        if not data.get('last_name'):
            raise serializers.ValidationError("Нужно указать фамилию")
        return data


class ChangeUserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        if models.User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Эта эл. почта уже используется")
        return value

    def validate(self, data):
        if not data.get('email'):
            raise serializers.ValidationError("Нужно указать эл. почту.")
        return data


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})


class UserInvitationSerializer(UserCreateSerializer):
    invite_code = serializers.CharField(required=True)

    class Meta(UserCreateSerializer.Meta):
        fields = UserCreateSerializer.Meta.fields + ['invite_code']

    def validate_invite_code(self, value):
        invitation = Invitation.objects.filter(invite_code=value).first()
        if invitation and not invitation.is_used:
            return value
        else:
            raise serializers.ValidationError("Неверный код приглашения")


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.UUIDField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Пароли не совпадают.")
        return data
