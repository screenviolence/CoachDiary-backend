from django.db.models.signals import post_save
from django.dispatch import receiver

from students.models import Student
from standards.models import Standard, Level, StudentStandard


@receiver(post_save, sender=Student)
def create_student_standards(sender, instance, created, **kwargs):
    """
    Создает записи StudentStandard для нового студента при его создании
    """
    if created:
        standards = Standard.objects.filter(who_added=instance.student_class.class_owner)
        student_class_numbers = instance.student_class.number
        gender = instance.gender

        for standard in standards:
            for student_class_number in range(1, student_class_numbers + 1):
                level = Level.objects.filter(
                    standard=standard,
                    level_number=student_class_number,
                    gender=gender
                ).first()

                if level:
                    StudentStandard.objects.create(
                        student=instance,
                        standard=standard,
                        level=level,
                        value=None,
                        grade=None
                    )


@receiver(post_save, sender=Level)
def create_standards_when_level_created(sender, instance, created, **kwargs):
    """
    Создает записи StudentStandard когда создается новый уровень
    """
    if created:
        standard = instance.standard
        gender = instance.gender
        level_number = instance.level_number

        # Находим студентов этого пола, в классе не ниже данного уровня
        students = Student.objects.filter(
            student_class__class_owner=standard.who_added,
            gender=gender,
            student_class__number__gte=level_number
        )

        for student in students:
            if student.student_class.number >= level_number:
                StudentStandard.objects.create(
                    student=student,
                    standard=standard,
                    level=instance,
                    value=None,
                    grade=None
                )
