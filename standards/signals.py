from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from students.models import Student, StudentClass
from standards.models import Standard, Level, StudentStandard


def create_student_standard_entries(student, standards, level_filters=None, class_range=None):
    """
    Общая функция для создания записей StudentStandard

    Args:
        student: объект студента
        standards: queryset стандартов
        level_filters: дополнительные фильтры для уровней
        class_range: диапазон классов для создания записей
    """
    to_create = []
    gender = student.gender

    base_filter = {'gender': gender}
    if level_filters:
        base_filter.update(level_filters)

    if not class_range:
        class_range = [student.student_class.number]

    for standard in standards:
        for class_num in class_range:
            base_filter.update({
                'standard': standard,
                'level_number': class_num
            })

            level = Level.objects.filter(**base_filter).first()
            if not level:
                continue

            exists = StudentStandard.objects.filter(
                student=student,
                standard=standard,
                level=level
            ).exists()

            if not exists:
                to_create.append(
                    StudentStandard(
                        student=student,
                        standard=standard,
                        level=level,
                        value=None,
                        grade=None
                    )
                )

    if to_create:
        StudentStandard.objects.bulk_create(to_create)


@receiver(pre_save, sender=Student)
def check_class_change(sender, instance, **kwargs):
    """Проверяет, изменился ли класс студента"""
    if instance.pk:
        try:
            old_instance = Student.objects.get(pk=instance.pk)
            if old_instance.student_class.number != instance.student_class.number:
                update_standards_on_class_change(
                    instance,
                    old_class_number=old_instance.student_class.number,
                    new_class_number=instance.student_class.number
                )
        except Student.DoesNotExist:
            pass


@receiver(post_save, sender=StudentClass)
def handle_student_class_change(sender, instance, **kwargs):
    """Обрабатывает изменения в классе и обновляет стандарты для всех студентов"""
    class_owner = instance.class_owner
    class_number = instance.number

    students = Student.objects.filter(
        student_class=instance,
        student_class__class_owner=class_owner
    )

    standards = Standard.objects.filter(who_added=class_owner)

    for student in students:
        create_student_standard_entries(
            student=student,
            standards=standards,
            class_range=[class_number]
        )


def update_standards_on_class_change(student, old_class_number, new_class_number):
    """Создает стандарты при смене класса"""
    if new_class_number > old_class_number:
        standards = Standard.objects.filter(who_added=student.student_class.class_owner)
        create_student_standard_entries(
            student=student,
            standards=standards,
            class_range=range(old_class_number + 1, new_class_number + 1)
        )


@receiver(post_save, sender=Student)
def create_student_standards(sender, instance, created, **kwargs):
    """Создает записи StudentStandard для нового студента при его создании"""
    if created:
        standards = Standard.objects.filter(who_added=instance.student_class.class_owner)
        student_class_number = instance.student_class.number

        create_student_standard_entries(
            student=instance,
            standards=standards,
            class_range=range(1, student_class_number + 1)
        )


@receiver(post_save, sender=Level)
def create_standards_when_level_created(sender, instance, created, **kwargs):
    """Создает записи StudentStandard когда создается новый уровень"""
    if created:
        standard = instance.standard
        gender = instance.gender
        level_number = instance.level_number

        students = Student.objects.filter(
            student_class__class_owner=standard.who_added,
            gender=gender,
            student_class__number__gte=level_number
        )

        to_create = []
        for student in students:
            if student.student_class.number >= level_number:
                exists = StudentStandard.objects.filter(
                    student=student,
                    standard=standard,
                    level=instance
                ).exists()

                if not exists:
                    to_create.append(
                        StudentStandard(
                            student=student,
                            standard=standard,
                            level=instance,
                            value=None,
                            grade=None
                        )
                    )

        if to_create:
            StudentStandard.objects.bulk_create(to_create)