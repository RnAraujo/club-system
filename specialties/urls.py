from django.urls import path
from . import views

app_name = 'specialties'

urlpatterns = [
    # Especialidades
    path('', views.SpecialtyListView.as_view(), name='list'),
    path('create/', views.SpecialtyCreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.SpecialtyUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.SpecialtyDeleteView.as_view(), name='delete'),

    # Programaciones
    path('schedules/create/', views.ScheduleCreateView.as_view(), name='schedule_create'),
    path('schedules/<int:pk>/update/', views.ScheduleUpdateView.as_view(), name='schedule_update'),
    path('schedules/<int:pk>/delete/', views.ScheduleDeleteView.as_view(), name='schedule_delete'),
]