import uuid

from django.db.models import Count
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from students.models import Student, Invitation, StudentClass


@receiver(post_save, sender=Student)
def create_invitation(sender, instance, created, **kwargs):
    """Создает приглашение для нового студента."""
    if created:
        if not hasattr(instance, 'invitation'):
            invite_code = uuid.uuid4().hex[:8].upper()
            Invitation.objects.create(
                student=instance,
                invite_code=invite_code,
                is_used=False
            )


@receiver(post_delete, sender=Student)
@receiver(post_save, sender=Student)
def clean_empty_classes(sender, instance, **kwargs):
    """
    Находит и удаляет все пустые классы после изменений студентов.
    """
    empty_classes = StudentClass.objects.annotate(
        student_count=Count('students')
    ).filter(student_count=0)

    empty_classes.delete()