from django.urls import include, path
from rest_framework import routers

from . import views

standards_router = routers.DefaultRouter()
standards_router.register(r"standards", views.StandardValueViewSet, basename="students-standards")
standards_router.register(r"students/(?P<student_id>\d+)/standards",
                          views.StudentStandardsViewSet,
                          basename="student-standards")
standards_router.register(r'students/results/list', views.StudentsResultsViewSet, basename='students-results')

standards_router.register(r'students/results/create', views.StudentResultsCreateOrUpdateViewSet,
                          basename='students-results-create')

urlpatterns = [
    path("", include(standards_router.urls)),

]
