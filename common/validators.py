from rest_framework.exceptions import ValidationError


class ComplexPasswordValidator:
    def validate(self, password, user=None):
        if len(password) < 8:
            raise ValidationError("Пароль должен содержать не менее 8 символов")

        if not any(char.isupper() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву")

        if not any(char.isdigit() for char in password):
            raise ValidationError("Пароль должен содержать хотя бы одну цифру")

    def get_help_text(self):
        return "Пароль должен содержать не менее 8 символов, включая хотя бы одну заглавную букву и одну цифру."
