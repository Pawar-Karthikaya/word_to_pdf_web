from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('api/upload/', views.upload_and_convert, name='upload_convert'),
    path('api/task/<uuid:task_id>/', views.check_status, name='check_status'),
    path('api/download/<uuid:task_id>/', views.download_file, name='download_file'),
    path('api/cleanup/', views.cleanup, name='cleanup'),
]