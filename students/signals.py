import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver

from students.models import Student, Invitation


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
