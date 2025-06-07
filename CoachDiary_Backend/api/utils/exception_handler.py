from django.http import JsonResponse
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, AuthenticationFailed
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, (NotAuthenticated, AuthenticationFailed)):
        return JsonResponse(
            {"detail": "Требуется аутентификация."},
            status=status.HTTP_401_UNAUTHORIZED
        )

    if response is not None:
        response.data = {
            "status": "Произошла ошибка",
            "details": response.data,
        }

    return response
