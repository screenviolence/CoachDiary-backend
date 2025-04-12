from django.urls import include, path
from rest_framework import routers

from . import views

student_router = routers.DefaultRouter()
student_router.register(r"students", views.StudentViewSet, basename="students")
student_router.register(r"classes", views.StudentClassViewSet, basename="classes")

urlpatterns = [
    path("", include(student_router.urls)),

]
