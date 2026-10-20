from django.urls import path
from . import views

app_name = 'specialties'

urlpatterns = [
    path('', views.SpecialtyListView.as_view(), name='list'),
    path('create/', views.SpecialtyCreateView.as_view(), name='create'),
    path('schedule/create/', views.ScheduleCreateView.as_view(), name='schedule_create'),
]