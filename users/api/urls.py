from django.urls import path

from .views import UserLoginView, UserViewSet, UserProfileViewSet, UserLogoutView, JoinByInvitationView

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("login/", UserLoginView.as_view({'get': 'get', 'post': 'post'}), name="UserLogin"),
    path("create-user/", UserViewSet.as_view({"post": "create"}), name="UserCreate"),
    path("profile/", UserProfileViewSet.as_view({'get': 'list', 'put': 'change_password', 'patch': 'change_details'}),
         name="UserProfile"),
    path("logout/", UserLogoutView.as_view({'post': 'logout'}), name="UserLogout"),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('create-user/from-invitation/<str:invite_code>/',
         JoinByInvitationView.as_view({'get': 'list', 'post': 'create'}),
         name='create_user_from_invitation'),

]
