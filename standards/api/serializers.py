from rest_framework import serializers, exceptions
from rest_framework.exceptions import ValidationError

from auth.users.api.serializers import UserSerializer
from coachdiary.api.utils.serializers import get_id_serializer_for_model
from drf_writable_nested.serializers import WritableNestedModelSerializer

from .. import models


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Level
        fields = (
            "id",
            "level_number",
            "low_level_value",
            "middle_level_value",
            "high_level_value",
            "gender"
        )
        read_only_fields = (
            "id",
        )


# class StandardValueSerializer(WritableNestedModelSerializer):
#     standard = StandardSerializer()
#     student_class = get_id_serializer_for_model(models.StudentClass)
#     levels = LevelSerializer(many=True)
#
#     class Meta:
#         model = models.StandardValue
#         fields = (
#             "id",
#             "standard",
#             "levels"
#         )
#         read_only_fields = (
#             "id",
#         )

# def validate(self, attrs: dict):
#     if "standard" in attrs and "has_numeric_value" in attrs["standard"]:
#         levels_data = attrs.get("levels", [])
#         is_numeric_value = attrs["standard"]["has_numeric_value"]
#
#         if is_numeric_value:
#             for level in levels_data:
#                 if any([level.get('low_level_value') is not None,
#                         level.get('middle_level_value') is not None,
#                         level.get('high_level_value') is not None]):
#                     raise exceptions.ValidationError(
#                         "Для навыков не поддерживаются значения уровней. "
#                         "Заполните только номер уровня."
#                     )
#         else:
#             for level in levels_data:
#                 if not all([level.get('low_level_value') is not None,
#                             level.get('middle_level_value') is not None,
#                             level.get('high_level_value') is not None]):
#                     raise exceptions.ValidationError(
#                         "Для нормативов необходимо задать значения уровней: "
#                         "Минимальное, Среднее и Лучшее."
#                     )
#
#     return super().validate(attrs)

# def create(self, validated_data: dict):
#     levels_data = validated_data.pop("levels", [])
#     standard = super().create(validated_data)
#
#     for single_level_data in levels_data:
#         standard.levels.create(**single_level_data)
#
#     return standard


class StudentClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StudentClass
        fields = ("id", "class_name", "number", "recruitment_year")

    def create(self, validated_data):
        request_user = self.context['request'].user
        student_class, created = models.StudentClass.objects.get_or_create(
            number=validated_data['number'],
            class_name=validated_data['class_name'],
            defaults={'class_owner': request_user}
        )

        return student_class

    def update(self, instance, validated_data):
        request_user = self.context['request'].user

        if instance.class_owner != request_user:
            raise ValidationError("Only the class owner can update this class.")

        # Update instance fields with validated data
        instance.number = validated_data.get('number', instance.number)
        instance.class_name = validated_data.get('class_name', instance.class_name)

        # Ensure the class_owner is set to the current user
        instance.class_owner = request_user

        # Save the updated instance
        instance.save()
        return instance


class FullClassNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.StudentClass
        fields = ('id', 'number', 'class_name')


class StandardSerializer(serializers.ModelSerializer):
    levels = LevelSerializer(many=True)

    class Meta:
        model = models.Standard
        fields = ['id', 'name', 'has_numeric_value', 'levels']

    def validate(self, attrs):
        if "has_numeric_value" in attrs:
            levels_data = attrs.get("levels", [])
            is_numeric_value = attrs["has_numeric_value"]

            if is_numeric_value:
                for level in levels_data:
                    if not all([
                        level.get('low_level_value') is not None,
                        level.get('middle_level_value') is not None,
                        level.get('high_level_value') is not None
                    ]):
                        raise serializers.ValidationError(
                            "Для нормативов необходимо задать значения уровней: "
                            "Минимальное, Среднее и Лучшее."

                        )
            else:
                for level in levels_data:
                    if any([
                        level.get('low_level_value') is not None,
                        level.get('middle_level_value') is not None,
                        level.get('high_level_value') is not None
                    ]):
                        raise serializers.ValidationError(
                            "Для навыков не поддерживаются значения уровней. "
                            "Заполните только номер уровня."
                        )

        return super().validate(attrs)

    def create(self, validated_data):
        levels_data = validated_data.pop("levels", [])
        request_user = self.context['request'].user
        standard = models.Standard.objects.create(who_added=request_user, **validated_data)

        for single_level_data in levels_data:
            models.Level.objects.create(standard=standard, **single_level_data)

        return standard

    def update(self, instance, validated_data):
        levels_data = validated_data.pop('levels', [])
        instance.name = validated_data.get('name', instance.name)
        instance.has_numeric_value = validated_data.get('has_numeric_value', instance.has_numeric_value)
        instance.save()

        existing_levels = {level.id: level for level in instance.levels.all()}
        new_levels = []

        for single_level_data in levels_data:
            level_id = single_level_data.get('id')
            if level_id and level_id in existing_levels:
                level = existing_levels.pop(level_id)
                level.level_number = single_level_data.get('level_number', level.level_number)
                level.low_level_value = single_level_data.get('low_level_value', level.low_level_value)
                level.middle_level_value = single_level_data.get('middle_level_value', level.middle_level_value)
                level.high_level_value = single_level_data.get('high_level_value', level.high_level_value)
                level.gender = single_level_data.get('gender', level.gender)
                level.save()
            else:
                new_levels.append(models.Level(standard=instance, **single_level_data))

        for level in existing_levels.values():
            level.delete()

        models.Level.objects.bulk_create(new_levels)

        return instance


class StudentStandardSerializer(serializers.ModelSerializer):
    standard = StandardSerializer()

    class Meta:
        model = models.StudentStandard
        fields = (
            'standard',
            'grade',
            'value',
            'level')


class StudentSerializer(WritableNestedModelSerializer):
    student_class = StudentClassSerializer()

    class Meta:
        model = models.Student
        fields = ("id", "full_name", "student_class", "birthday", "gender")

    def create(self, validated_data):
        student_class_data = validated_data.pop('student_class')
        request_user = self.context['request'].user

        class_instance = self.get_or_create_class(student_class_data, request_user)

        student = models.Student.objects.create(student_class=class_instance, **validated_data)
        return student

    def update(self, instance, validated_data):
        student_class_data = validated_data.pop('student_class', None)
        request_user = self.context['request'].user

        if student_class_data:
            class_instance = self.get_or_create_class(student_class_data, request_user)
            instance.student_class = class_instance

        instance.full_name = validated_data.get('full_name', instance.full_name)
        instance.birthday = validated_data.get('birthday', instance.birthday)
        instance.gender = validated_data.get('gender', instance.gender)
        instance.save()

        return instance

    def get_or_create_class(self, student_class_data, request_user):
        class_instance = models.StudentClass.objects.filter(
            number=student_class_data['number'],
            class_name=student_class_data['class_name'],
            class_owner=request_user
        ).first()

        if not class_instance:
            class_instance = models.StudentClass.objects.create(
                number=student_class_data['number'],
                class_name=student_class_data['class_name'],
                class_owner=request_user
            )

        return class_instance


class StudentResultSerializer(serializers.ModelSerializer):
    student_class = FullClassNameSerializer()
    student_standards = StudentStandardSerializer(source='studentstandard_set', many=True)
    levels = LevelSerializer(source='level_set', many=True)

    class Meta:
        model = models.Student
        fields = ['id', 'full_name', 'student_class', 'birthday', 'gender', 'student_standards', 'levels']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        # Include levels for each student standard
        if representation.get('student_standards'):
            levels = []
            for standard in representation['student_standards']:
                if 'level' in standard and standard['level']:
                    levels.append(standard['level'])
                representation.update(standard)
            representation['levels'] = levels
            representation.pop('student_standards')

        return representation


class StudentStandardCreateSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(write_only=True)
    standard_id = serializers.IntegerField(write_only=True)
    level_id = serializers.IntegerField(write_only=True, required=False)
    level_number = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = models.StudentStandard
        fields = ['student_id', 'standard_id', 'value', 'grade', 'level_id', 'level_number']
        read_only_fields = ['grade']

    def validate(self, data):
        student_id = data.get('student_id')
        standard_id = data.get('standard_id')
        value = data.get('value')
        level_id = data.get('level_id')
        level_number = data.get('level_number')

        try:
            student = models.Student.objects.get(id=student_id)
        except models.Student.DoesNotExist:
            raise serializers.ValidationError("Student does not exist")

        try:
            standard = models.Standard.objects.get(id=standard_id)
        except models.Standard.DoesNotExist:
            raise serializers.ValidationError("Standard does not exist")

        # Automatically set the level_id if not provided
        if level_id is None:
            if level_number is not None:
                try:
                    level = models.Level.objects.get(
                        level_number=level_number,
                        standard=standard,
                        gender=student.gender
                    )
                    level_id = level.id
                except models.Level.DoesNotExist:
                    raise serializers.ValidationError(
                        "Invalid level for the provided level number and student's gender")
            else:
                try:
                    level = models.Level.objects.get(
                        level_number=student.student_class.number,
                        standard=standard,
                        gender=student.gender
                    )
                    level_id = level.id
                    print(level.level_number)
                except models.Level.DoesNotExist:
                    raise serializers.ValidationError("Invalid level for the student's class")

        # Ensure level_id is valid
        try:
            level = models.Level.objects.get(id=level_id)
        except models.Level.DoesNotExist:
            raise serializers.ValidationError("Invalid level_id")

        # Determine the grade based on the value
        if not standard.has_numeric_value:
            data['grade'] = value
        else:
            if value >= level.low_level_value:
                if value >= level.high_level_value:
                    data['grade'] = '5'
                elif value >= level.middle_level_value:
                    data['grade'] = '4'
                else:
                    data['grade'] = '3'
            else:
                data['grade'] = '2'  # Default to the lowest grade if value is below low_level_value

        data['student'] = student
        data['standard'] = standard
        data['level'] = level

        return data

    def create(self, validated_data):
        student_standard, created = models.StudentStandard.objects.update_or_create(
            student=validated_data['student'],
            standard=validated_data['standard'],
            defaults={
                'value': validated_data['value'],
                'grade': validated_data['grade'],
                'level': validated_data['level']
            }
        )
        return student_standard
