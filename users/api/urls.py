from django.urls import path

from .views import UserLoginView, UserViewSet, UserProfileViewSet, UserLogoutView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="UserLogin"),
    path("create-user/", UserViewSet.as_view({"post": "create"}), name="UserCreate"),
    path("profile/", UserProfileViewSet.as_view(), name="UserProfile"),
    path("logout/", UserLogoutView.as_view(), name="UserLogout"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
