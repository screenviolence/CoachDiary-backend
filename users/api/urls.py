from django.urls import path

from .views import UserLoginView, UserViewSet, UserProfileViewSet, UserLogoutView

urlpatterns = [
    path("login/", UserLoginView.as_view(), name="UserLogin"),
    path("create-user/", UserViewSet.as_view({"post": "create"}), name="UserCreate"),
    path("profile/", UserProfileViewSet.as_view(), name="UserProfile"),
    path("logout/", UserLogoutView.as_view(), name="UserLogout")
]