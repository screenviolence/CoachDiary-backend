from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def send_verification_email(user):
    """
    Отправляет email со ссылкой для подтверждения адреса электронной почты.
    """
    context = {
        'username': user.full_name,
        'verification_url': f"{settings.SITE_URL}/verify-email/{user.verification_token}/",
    }

    html_message = render_to_string('verification_email.html', context)
    plain_message = strip_tags(html_message)

    response = send_mail(
        subject='Подтверждение адреса электронной почты',
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    print(response)


def send_password_reset_email(user):
    """Отправка email с инструкциями по сбросу пароля"""

    context = {
        'username': user.full_name,
        'reset_url': f"{settings.SITE_URL}/reset-password/{user.password_reset_token}/"
    }

    html_message = render_to_string('change_password_email.html', context)
    plain_message = strip_tags(html_message)

    response = send_mail(
        subject="Сброс пароля",
        message=plain_message,
        from_email=settings.EMAIL_HOST_USER,
        auth_user=settings.EMAIL_HOST_USER,
        auth_password=settings.EMAIL_HOST_PASSWORD,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )
    print(response)
