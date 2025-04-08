from django.contrib.auth.hashers import check_password
from rest_framework import serializers

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
            "full_name"
        )


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    patronymic = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = models.User
        fields = [
            'email',
            'password',
            'confirm_password',
            'first_name',
            'last_name',
            'patronymic'
        ]

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')

        email = validated_data.pop('email')
        password = validated_data.pop('password')
        first_name = validated_data.pop('first_name')
        last_name = validated_data.pop('last_name')
        patronymic = validated_data.pop('patronymic', None)

        user = models.User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic
        )

        return user


class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)
    confirm_new_password = serializers.CharField(required=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError("Passwords doesn't match.")
        if not check_password(data['current_password'], self.context['request'].user.password):
            raise serializers.ValidationError("Current password is incorrect.")
        return data


class ChangeUserDetailsSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False)
    name = serializers.CharField(required=False)

    def validate_email(self, value):
        if models.User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate(self, data):
        if not data.get('email') and not data.get('name'):
            raise serializers.ValidationError("At least one field (email or name) must be provided.")
        return data
