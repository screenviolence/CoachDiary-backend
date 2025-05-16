import uuid

from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import User
from users.utils import send_verification_email


@receiver(post_save, sender=User)
def send_confirmation_email(sender, instance, created, **kwargs):
    """Отправляет письмо подтверждения на почту пользователя."""
    if created:
        if not instance.is_email_verified:
            instance.verification_token = uuid.uuid4()
            instance.save()
            send_verification_email(instance)