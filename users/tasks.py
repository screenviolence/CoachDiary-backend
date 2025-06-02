from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


@shared_task
def send_verification_email_task(email, full_name, verification_token):
    """Асинхронная отправка email для подтверждения адреса"""
    context = {
        'username': full_name,
        'verification_url': f"{settings.SITE_URL}/verify-email/{verification_token}/",
        'service_url': settings.SITE_URL,
        'logo_url': f"{settings.SITE_URL}/logo.jpg",
    }

    html_message = render_to_string('verification_email.html', context)
    plain_message = strip_tags(html_message)

    return send_mail(
        subject='Подтверждение адреса электронной почты',
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )


@shared_task
def send_password_reset_email_task(email, full_name, reset_token):
    """Асинхронная отправка email для сброса пароля"""
    context = {
        'username': full_name,
        'reset_url': f"{settings.SITE_URL}/reset-password/{reset_token}/",
        'service_url': settings.SITE_URL,
        'logo_url': f"{settings.SITE_URL}/logo.jpg",
    }

    html_message = render_to_string('change_password_email.html', context)
    plain_message = strip_tags(html_message)

    return send_mail(
        subject="Сброс пароля",
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD,
        recipient_list=[email],
        html_message=html_message,
        fail_silently=False,
    )