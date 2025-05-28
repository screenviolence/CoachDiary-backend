from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import UserLoginView, UserViewSet, UserProfileViewSet, UserLogoutView, JoinByInvitationView, \
    VerifyEmailView, PasswordResetViewSet, TeacherImportExportViewSet, ResendConformationEmailView

user_router = routers.DefaultRouter()
user_router.register(r'login', UserLoginView, basename='login')
user_router.register(r'create-user', UserViewSet, basename='user-create')
user_router.register(r'profile', UserProfileViewSet, basename='user-profile')
user_router.register(r'logout', UserLogoutView, basename='user-logout')
user_router.register(r'create-user/from-invitation', JoinByInvitationView, basename='create-user-from-invitation')
user_router.register(r'email/reset-password', PasswordResetViewSet, basename='reset-password')
user_router.register(r'profile', TeacherImportExportViewSet, basename='import-export')
user_router.register(r'email/resend-confirmation', ResendConformationEmailView, basename='users')
urlpatterns = [
    path("", include(user_router.urls)),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('email/verify-email/<uuid:token>/', VerifyEmailView.as_view({'get': 'list'}), name='verify-email'),
]
