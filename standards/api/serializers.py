from rest_framework import serializers

from students.api.serializers import FullClassNameSerializer
from students.models import Student
from .. import models


class LevelSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Level
        fields = (
            "id",
            "is_lower_better",
            "level_number",
            "low_value",
            "middle_value",
            "high_value",
            "gender"
        )
        read_only_fields = (
            "id",
        )


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
                        level.get('low_value') is not None,
                        level.get('middle_value') is not None,
                        level.get('high_value') is not None
                    ]):
                        raise serializers.ValidationError(
                            "Для нормативов необходимо задать значения уровней: "
                            "Минимальное, Среднее и Лучшее."

                        )
            else:
                for level in levels_data:
                    if any([
                        level.get('low_value') is not None,
                        level.get('middle_value') is not None,
                        level.get('high_value') is not None
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
                level.low_value = single_level_data.get('low_value', level.low_value)
                level.middle_value = single_level_data.get('middle_value', level.middle_value)
                level.high_value = single_level_data.get('high_value', level.high_value)
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


class StudentResultSerializer(serializers.ModelSerializer):
    student_class = FullClassNameSerializer()

    class Meta:
        model = Student
        fields = ['id', 'first_name', 'last_name', 'patronymic', 'full_name', 'student_class', 'birthday', 'gender']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        standard_ids = self.context.get('standard_ids', [])

        if standard_ids:
            values = []
            grades = []
            standards_details = []

            for standard_id in standard_ids:
                try:
                    student_standard = instance.standards.get(
                        standard_id=standard_id,
                        level__level_number=instance.student_class.number,
                        level__gender=instance.gender
                    )

                    standard_detail = {
                        'standard_id': int(standard_id),
                        'value': student_standard.value,
                        'grade': student_standard.grade
                    }

                    if student_standard.value is not None:
                        values.append(student_standard.value)
                    if student_standard.grade is not None:
                        grades.append(student_standard.grade)

                except:
                    standard_detail = {
                        'standard_id': int(standard_id),
                        'value': None,
                        'grade': None
                    }

                standards_details.append(standard_detail)

            representation['average_value'] = sum(values) / len(values) if values else None
            representation['average_grade'] = sum(grades) / len(grades) if grades else None
            representation['standards_details'] = standards_details

        return representation


class StudentStandardCreateSerializer(serializers.ModelSerializer):
    student_id = serializers.IntegerField(write_only=True)
    standard_id = serializers.IntegerField(write_only=True)
    level_number = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = models.StudentStandard
        fields = ['student_id', 'standard_id', 'value', 'grade', 'level_id', 'level_number']
        read_only_fields = ['grade']

    def validate(self, data):
        student_id = data.get('student_id')
        standard_id = data.get('standard_id')
        value = data.get('value')
        level_number = data.get('level_number')

        try:
            student = Student.objects.get(id=student_id)
        except Student.DoesNotExist:
            raise serializers.ValidationError("Student does not exist")

        try:
            standard = models.Standard.objects.get(id=standard_id)
        except models.Standard.DoesNotExist:
            raise serializers.ValidationError("Standard does not exist")

        if level_number is not None:
            try:
                level = models.Level.objects.get(
                    level_number=level_number,
                    standard=standard,
                    gender=student.gender
                )
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
            except models.Level.DoesNotExist:
                raise serializers.ValidationError("Invalid level for the student's class")

        data['grade'] = models.Level.calculate_grade(level, value)
        data['student'] = student
        data['standard'] = standard
        data['level'] = level

        return data

    def create(self, validated_data):
        level = validated_data['level']

        student_standard, created = models.StudentStandard.objects.update_or_create(
            student=validated_data['student'],
            standard=validated_data['standard'],
            level=level,
            defaults={
                'value': validated_data['value'],
                'grade': validated_data['grade'],
            }
        )
        return student_standard


class StandardInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Standard
        fields = ('id', 'name', 'has_numeric_value')


class StudentStandardItemSerializer(serializers.ModelSerializer):
    standard = StandardInfoSerializer()
    level_number = serializers.SerializerMethodField()

    class Meta:
        model = models.StudentStandard
        fields = ('standard', 'level_number', 'value', 'grade')

    def get_level_number(self, obj):
        return obj.level.level_number if obj.level else None


class StudentStandardsResponseSerializer(serializers.Serializer):
    standards = StudentStandardItemSerializer(many=True)
    summary_grade = serializers.FloatField()
