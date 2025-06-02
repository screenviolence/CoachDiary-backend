from .tasks import send_verification_email_task, send_password_reset_email_task


def send_verification_email(user):
    """Запускает асинхронную задачу отправки email для подтверждения адреса"""
    send_verification_email_task.delay(
        user.email, 
        user.full_name, 
        user.verification_token
    )


def send_password_reset_email(user):
    """Запускает асинхронную задачу отправки email для сброса пароля"""
    send_password_reset_email_task.delay(
        user.email, 
        user.full_name, 
        user.password_reset_token
    )