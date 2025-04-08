from users.api.urls import urlpatterns as users_api_urlpatterns
#from standards.api.urls import urlpatterns as standards_api_urlpatterns
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from django.urls import path

urlpatterns = [
    *users_api_urlpatterns,
    #*standards_api_urlpatterns,
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'),name='docs'),
]