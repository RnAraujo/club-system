from django.urls import path
from . import views

app_name = 'registrations'

urlpatterns = [
    path('', views.RegistrationListView.as_view(), name='list'),
    path('create/', views.RegistrationCreateView.as_view(), name='create'),
    path('process/', views.ProcessListView.as_view(), name='process'),
    path('process/<int:club_id>/close/', views.close_process_view, name='process_close'),
    path('process/<int:club_id>/reopen/', views.reopen_process_view, name='process_reopen'),
]