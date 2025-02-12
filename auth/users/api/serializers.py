from django.contrib.auth.hashers import check_password
from rest_framework import serializers

from .. import models


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = (
            "id",
            "email",
            "name"
        )


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = models.User
        fields = ['email', 'password', 'confirm_password', 'name']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = models.User.objects.create_user(**validated_data)
        user.name = validated_data.get('name')
        user.save()
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
